#include <Arduino.h>


void lin_init(){
    error_lin = false;
    error_mech = false;
    error_midDead = false;
    for (size_t i = 0; i < print_array_size; ++i) {
    error_lin_index[i] = false;
    lin_max = 0;
    lin_min = 0;
    }
}
    

float lerp_dead(int32_t x, int32_t d1, int32_t d2){
  if(d1 == d2){
    return 0;
  } else {
    return (float)(x - d1) / (float)(d2 - d1);
  }
}

float dead_soll_volt_deg(float deg, float tarVolt,
                      float d12Deg, float d21Deg, float d22Deg, float d31Deg) {
  const float half = tarVolt * 0.5f;
  if (deg <= d12Deg) return 0.0f;
  if (deg <= d21Deg) return half * (deg - d12Deg) / (d21Deg - d12Deg);
  if (deg <= d22Deg) return half;
  if (deg <= d31Deg) return half + half * (deg - d22Deg) / (d31Deg - d22Deg);
  return tarVolt;
}

float corr_measure(float current_volt){
  cancelled = false;
  Serial.println("VOLTR");
  delay(50);
  if(cancelled == false){
    for(;;){
    String VCommand = Serial.readStringUntil('\n');
    VCommand.trim();
      if(VCommand.startsWith("ISTV:")){
        current_volt = VCommand.substring(5).toFloat();
        break;
      }
    }
  }
  return current_volt;
}

// dead_direction 0 -> deadzone links von position //////--- ;;; 1 -> rechts von position ---//////
float correction_movement(float &current_volt, float goal_volt, int dead_direction = 0, int timeout = 8000){
  const float v_tol = 0.001f;        
  const int32_t tick_tol = 1;
  int32_t low, high;
  current_volt = corr_measure(current_volt);

  while (!cancelled && fabsf(current_volt - goal_volt) <= v_tol) {
    int32_t t = 0;
    int32_t back = 0;
    if(dead_direction == 0){ // dead links
      t = get_tick_position() + 20;
      back = t - 50;
    } else if(dead_direction == 1){ // dead rechts
      t = get_tick_position() - 20;
      back = t + 50;
    }
    dxl.setGoalPosition(DID, back, UNIT_RAW);
    reached_goal(DID, back, 6);
    dxl.setGoalPosition(DID, t, UNIT_RAW);
    reached_goal(DID, t, 6);
    current_volt = corr_measure(current_volt);
  }

  high = get_tick_position();

  while (!cancelled && fabsf(current_volt - goal_volt) > v_tol) {
    int32_t t = 0;
    int32_t back = 0;
    if(dead_direction == 0){
      t = get_tick_position() - 10;
      back = t - 50;
    } else if(dead_direction == 1){
      t = get_tick_position() + 10;
      back = t + 50;
    }
    dxl.setGoalPosition(DID, back, UNIT_RAW);
    reached_goal(DID, back, 6);
    dxl.setGoalPosition(DID, t, UNIT_RAW);
    reached_goal(DID, t, 6);
    current_volt = corr_measure(current_volt);
  }

  low = get_tick_position();

  while (!cancelled && abs(high - low) > tick_tol) {
    int32_t mid = (high + low) / 2;
    int32_t back = mid + 50;
    dxl.setGoalPosition(DID, back, UNIT_RAW);
    reached_goal(DID, back, 6);
    dxl.setGoalPosition(DID, mid, UNIT_RAW);
    reached_goal(DID, mid, 6);

    current_volt = corr_measure(current_volt);
    if (fabsf(current_volt - goal_volt) > v_tol) {
      high = mid;
    } else {
      low = mid;
    }
  }
  float edgeDeg = 0;
    if(dead_direction == 0){
      edgeDeg = tick_to_deg(low);
    } else if(dead_direction == 1){
      edgeDeg = tick_to_deg(high);
    }
  return edgeDeg;
}

void linearity_movement(){
  // 1° = 11.375 ticks
  // 1 Tick = 0.08791208791 °
  float realDegTotal = tick_to_deg(real_tick_total);
  if(realDegTotal < 298.0 || realDegTotal > 332.0) error_mech = true;
  // real_tick_total = deg_to_tick(realDegTotal); // ca. 331.2°
  soll_tick_total = deg_to_tick(soll_deg_total); // ca. 330°

  float midDegs = 25;
  real_mid_deg = realDegTotal/2;
  float sollMidDeg = soll_deg_total/2;
  int32_t midSteps = deg_to_tick(25); // ca. 284 Ticks
  int32_t realMid = real_tick_total/2;
  int32_t offsetVonSoll = (real_tick_total-soll_tick_total) / 2;
  
  for(int i = 0; i < 5; i++){ // UNBEDINGT FIXEN (maybe)
    dxl.ledOff(1);
    delay(100);
    dxl.ledOn(1);
    delay(100);
  } 

  d11_tick = deg_to_tick(d11_deg);
  d12_tick = deg_to_tick(d12_deg);
  d21_tick = deg_to_tick(d21_deg);
  d22_tick = deg_to_tick(d22_deg);
  d31_tick = deg_to_tick(d31_deg);
  d32_tick = deg_to_tick(d32_deg);

  float soll_Deg[] = {real_mid_deg,
     d22_deg, d22_deg+midDegs, d22_deg+2*midDegs, d22_deg+3*midDegs, d31_deg, realDegTotal,
      d21_deg, d21_deg-midDegs, d21_deg-2*midDegs, d21_deg-3*midDegs, d12_deg, 0};
  
  int32_t mercyTick = 10; // 10 Ticks vor jeweiligem Ende
  int32_t mercyStart = mercyTick;
  int32_t mercyEnd = real_tick_total - mercyTick;

  int32_t sim_tick [] = {realMid,
     d22_tick, d22_tick+midSteps, d22_tick+2*midSteps, d22_tick+3*midSteps, d31_tick, mercyEnd,
      d21_tick, d21_tick-midSteps, d21_tick-2*midSteps, d21_tick-3*midSteps, d12_tick, mercyStart};
  
  int32_t drive_tick[print_array_size];
  for(size_t i = 0; i<print_array_size; i++){    
    if(sim_tick[i] == realMid || sim_tick[i] == mercyEnd || sim_tick[i] == mercyStart){
      drive_tick[i] = sim_tick[i] + start_tick;
    } else {
      drive_tick[i] = sim_tick[i] + start_tick + offsetVonSoll;
    }
  }

  //set_dyna_speed(fastSpeed);
  for (size_t i = 0; i<print_array_size; i++) {
    int32_t tick = drive_tick[i];
    //DEBUG_SERIAL.print(tick);
    dxl.setGoalPosition(DID, tick, UNIT_RAW);
    if (!reached_goal(DID, tick, 6)) {
      // Strom-Trip -> sofort raus
      Serial.println("CANCEL");
      cancelled = true;
      break;
    }
    
    // LEERE ZELLEN
    int32_t relTick = tick - start_tick;
    empty_cells[i] = false;
    if(relTick == mercyStart || relTick == mercyEnd ||
       relTick == d21_tick + offsetVonSoll || relTick == d22_tick + offsetVonSoll){
        empty_cells[i] = true;
       }

    // SOLL-WINKEL
    if(relTick == realMid-9){
      print_soll_deg[i] = soll_Deg[i]-real_mid_deg;
    } else if(relTick == mercyEnd || relTick == mercyStart){
       print_soll_deg[i] = soll_Deg[i]-real_mid_deg;
    } else{
       print_soll_deg[i] = soll_Deg[i]-sollMidDeg;
    }

    // SOLL-SPANNUNG
    print_soll_volt[i] = dead_soll_volt_deg(soll_Deg[i], tar_volt, d12_deg, d21_deg, d22_deg, d31_deg);

    // IST-SPANNUNG
    if(relTick == mercyEnd){
      print_ist_volt[i] = ist_end_volt - ist_start_volt;
    } else if(relTick == mercyStart) {
      print_ist_volt[i] = 0;
    } else {
      print_ist_volt[i] = corr_measure(print_ist_volt[i]);
      if(relTick == realMid){
        ist_mid_volt = print_ist_volt[i];
      }
    }
    
    // IST-WINKEL
    if(relTick == realMid){
      print_ist_deg[i] = get_deg_position() - real_mid_deg - tick_to_deg(start_tick);
    } else if(relTick == mercyEnd){
      print_ist_deg[i] = real_mid_deg;
    } else if(relTick == mercyStart){
      print_ist_deg[i] = -real_mid_deg;
    } else if(relTick == d12_tick + offsetVonSoll){
      print_ist_deg[i] = correction_movement(print_ist_volt[i], ist_start_volt, 0) - tick_to_deg(start_tick) - real_mid_deg;
      ccw_links = print_ist_deg[i];
    } else if(relTick == d21_tick + offsetVonSoll){
      print_ist_deg[i] = correction_movement(print_ist_volt[i], ist_mid_volt, 1) - tick_to_deg(start_tick) - real_mid_deg;
      ccw_rechts = print_ist_deg[i];
    } else if(relTick == d22_tick + offsetVonSoll){
      print_ist_deg[i] = correction_movement(print_ist_volt[i], ist_mid_volt, 0) - tick_to_deg(start_tick) - real_mid_deg;
      cw_links = print_ist_deg[i];
    } else if(relTick == d31_tick + offsetVonSoll){
      print_ist_deg[i] = correction_movement(print_ist_volt[i], ist_end_volt, 1) - tick_to_deg(start_tick) - real_mid_deg;
      cw_rechts = print_ist_deg[i];
    }
    else{
      print_ist_deg[i] = get_deg_position() - real_mid_deg - tick_to_deg(start_tick);
    }
    
    // REALER WINKEL ZUR MITTE
    if(print_soll_deg[i] == 0){
      print_real_diff_mid[i] = 0;
    }
    else if(print_ist_deg[i] > 0){
      print_real_diff_mid[i] = print_ist_deg[i] - cw_links;
    } else if(print_ist_deg[i] < 0){
      print_real_diff_mid[i] = print_ist_deg[i] - ccw_rechts;
    } 
  }
  // --------------- ERROR MITTELANZAPFUNG
  if(fabsf((cw_links + ccw_rechts) - (d21_deg + d22_deg)) > 1.5){
    error_midDead = true;
  }
  // --------------- ÜBERGABE AN PYTHON
  for (size_t i = 0; i<print_array_size; i++) {
    Serial.print("Soll-Winkel:");
    Serial.print(print_soll_deg[i],1);
    Serial.print(";Soll-Spannung:");
    Serial.print(print_soll_volt[i],2);
    Serial.print(";Ist-Spannung:");
    Serial.print(print_ist_volt[i],3);
    Serial.print(";Ist-Winkel:");
    Serial.print(print_ist_deg[i],1);
    Serial.print(";DiffMid-Winkel:");
    Serial.println(print_real_diff_mid[i],1);
  }

  dxl.setGoalPosition(DID, 2047, UNIT_RAW);
  reached_goal(DID, 2047, 6);
  dxl.ledOff(DID);
}

// ----------------- LINEARITÄT
void calc_linearity(){
  const float realVoltPerDegree = tar_volt/ges_aktiv;
  const float midSollVoltReal = aktiv_ccw*realVoltPerDegree;

  for(size_t i = 0; i<print_array_size ; i++){
    // LEERE ZELLEN ÜBERSPRINGEN
    if (empty_cells[i] == true) {
      print_soll_volt_real[i] = NAN;
      print_linear_real[i] = NAN;
      continue;
    }

    // SOLLSPANNUNG REAL
    print_soll_volt_real[i] = print_real_diff_mid[i] * realVoltPerDegree + midSollVoltReal;
    
    // LINEARITÄT
    print_linear_real[i] = (print_ist_volt[i] - print_soll_volt_real[i])/tar_volt;
    if(fabsf(print_linear_real[i]) > 0.005) {
      error_lin = true;
      error_lin_index[i] = true;
    } 

    if(print_linear_real[i] > lin_max) {
      lin_max = print_linear_real[i];
    }
    if(print_linear_real[i] < lin_min) {
      lin_min = print_linear_real[i];
    }
  }

  
  for(size_t i = 0; i<print_array_size ; i++){
    Serial.print("LINEAR;");
    Serial.print("idx:");   
    Serial.print(i);
    Serial.print(";Soll-Spannung Real:");   
    Serial.print(print_soll_volt_real[i], 3);
    Serial.print(";Linearität:"); 
    Serial.println(print_linear_real[i], 6);
  }
}

void calc_summary(){
  float totzone = cw_links - ccw_rechts;
  aktiv_ccw = fabsf(ccw_links - ccw_rechts);
  aktiv_cw = (cw_rechts - cw_links);
  ges_aktiv = aktiv_ccw + aktiv_cw;

  Serial.print("SUMMARY;");
  Serial.print("Totzone:");   
  Serial.print(totzone, 1);
  Serial.print(";aktiv_cw:"); 
  Serial.print(aktiv_cw, 1);
  Serial.print(";aktiv_ccw:");
  Serial.print(aktiv_ccw, 1);
  Serial.print(";AktivSumme:");
  Serial.println(ges_aktiv, 1);
}

// ERROR AUSGABE EXCEL
void calc_errors(){
  if (error_lin == true) {
    Serial.print("ERROR_LIN;");
    Serial.print("IDX:");
    bool first = true;
    for (size_t i = 0; i < print_array_size; i++) {
      if (error_lin_index[i]) {
        if (first) {
          Serial.print(i);
          first = false;
        } else {
          Serial.print(",");
          Serial.print(i);
        }
      }
    }
    Serial.print(";LIN_MAX:");
    Serial.print(lin_max, 6);
    Serial.print(";LIN_MIN:");
    Serial.println(lin_min, 6);
  }
}