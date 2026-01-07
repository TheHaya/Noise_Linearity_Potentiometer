#include <Arduino.h>
#include <Dynamixel2Arduino.h>
#include <servo.h>
#include <calibrate.h>
#include <linearity.h>


// --------------- VARIABLES
int tar_volt = 10;

const size_t print_array_size = 13;
float print_ist_deg[print_array_size];
float print_soll_deg[print_array_size];
float print_soll_volt[print_array_size];
float print_ist_volt[print_array_size];
float print_real_diff_mid[print_array_size];
float print_soll_volt_real[print_array_size];
float print_linear_real[print_array_size];
bool empty_cells[print_array_size];
bool error_lin;
bool error_mech;
bool error_midDead;
bool error_lin_index[print_array_size];

int32_t real_tick_total, soll_tick_total;
float soll_deg_total;
float d11_deg, d12_deg, d21_deg, d22_deg, d31_deg, d32_deg;
int32_t d11_tick, d12_tick, d21_tick, d22_tick, d31_tick, d32_tick;
float ist_start_volt, ist_end_volt, ist_mid_volt;
float ccw_links, ccw_rechts, cw_links, cw_rechts, aktiv_ccw, aktiv_cw, ges_aktiv;
float real_mid_deg;
float lin_min, lin_max;


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

float dead_soll_volt_deg(float deg, float tar_volt,
                      float d12_deg, float d21_deg, float d22_deg, float d31_deg) {
  const float half = tar_volt * 0.5f;
  if (deg <= d12_deg) return 0.0f;
  if (deg <= d21_deg) return half * (deg - d12_deg) / (d21_deg - d12_deg);
  if (deg <= d22_deg) return half;
  if (deg <= d31_deg) return half + half * (deg - d22_deg) / (d31_deg - d22_deg);
  return tar_volt;
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
float correction_movement(float &current_volt, float goal_volt, 
                          int dead_direction, int timeout){
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
    drive_to(back, user_rpm);
    reached_goal(back, 2);
    drive_to(t, user_rpm);
    reached_goal(t, 2);
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
    drive_to(back, user_rpm);
    reached_goal(back, 2);
    drive_to(t, user_rpm);
    reached_goal(t, 2);
    current_volt = corr_measure(current_volt);
  }

  low = get_tick_position();

  while (!cancelled && abs(high - low) > tick_tol) {
    int32_t mid = (high + low) / 2;
    int32_t back = mid + 50;
    drive_to(back, user_rpm);
    reached_goal(back, 2);
    drive_to(mid, user_rpm);
    reached_goal(mid, 2);

    current_volt = corr_measure(current_volt);
    if (fabsf(current_volt - goal_volt) > v_tol) {
      high = mid;
    } else {
      low = mid;
    }
  }
  float edge_deg = 0;
    if(dead_direction == 0){
      edge_deg = tick_to_deg(low);
    } else if(dead_direction == 1){
      edge_deg = tick_to_deg(high);
    }
  return edge_deg;
}

void linearity_movement(){
  // 1° = 11.375 ticks
  // 1 Tick = 0.08791208791 °
  float real_deg_total = tick_to_deg(real_tick_total);
  if(real_deg_total < 298.0 || real_deg_total > 332.0) error_mech = true;
  // real_tick_total = deg_to_tick(real_deg_total); // ca. 331.2°
  soll_tick_total = deg_to_tick(soll_deg_total); // ca. 330°
  real_tick_total = end_tick - start_tick;

  float mid_degs = 25;
  real_mid_deg = real_deg_total/2;
  float soll_mid_deg = soll_deg_total/2;
  int32_t mid_steps = deg_to_tick(25); // ca. 284 Ticks
  int32_t real_mid = real_tick_total/2;
  int32_t offset_von_soll = (real_tick_total-soll_tick_total) / 2;
  
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
     d22_deg, d22_deg+mid_degs, d22_deg+2*mid_degs, d22_deg+3*mid_degs, d31_deg, real_deg_total,
      d21_deg, d21_deg-mid_degs, d21_deg-2*mid_degs, d21_deg-3*mid_degs, d12_deg, 0};
  
  int32_t mercy_tick = 10; // 10 Ticks vor jeweiligem Ende
  int32_t mercy_start = mercy_tick;
  int32_t mercy_end = real_tick_total - mercy_tick;

  int32_t sim_tick [] = {real_mid,
     d22_tick, d22_tick+mid_steps, d22_tick+2*mid_steps, d22_tick+3*mid_steps, d31_tick, mercy_end,
      d21_tick, d21_tick-mid_steps, d21_tick-2*mid_steps, d21_tick-3*mid_steps, d12_tick, mercy_start};
  
  int32_t drive_tick[print_array_size];
  for(size_t i = 0; i<print_array_size; i++){    
    if(sim_tick[i] == real_mid || sim_tick[i] == mercy_end || sim_tick[i] == mercy_start){
      drive_tick[i] = sim_tick[i] + start_tick;
    } else {
      drive_tick[i] = sim_tick[i] + start_tick + offset_von_soll;
    }
  }

  //set_dyna_speed(fastSpeed);
  for (size_t i = 0; i<print_array_size; i++) {
    int32_t tick = drive_tick[i];
    //DEBUG_SERIAL.print(tick);
    drive_to(tick, user_rpm);
    if (!reached_goal(tick, 2)) {
      // Strom-Trip -> sofort raus
      Serial.println("CANCEL");
      cancelled = true;
      break;
    }
    
    // LEERE ZELLEN
    int32_t rel_tick = tick - start_tick;
    empty_cells[i] = false;
    if(rel_tick == mercy_start || rel_tick == mercy_end ||
       rel_tick == d21_tick + offset_von_soll || rel_tick == d22_tick + offset_von_soll){
        empty_cells[i] = true;
       }

    // SOLL-WINKEL
    if(rel_tick == real_mid-9){
      print_soll_deg[i] = soll_Deg[i]-real_mid_deg;
    } else if(rel_tick == mercy_end || rel_tick == mercy_start){
       print_soll_deg[i] = soll_Deg[i]-real_mid_deg;
    } else{
       print_soll_deg[i] = soll_Deg[i]-soll_mid_deg;
    }

    // SOLL-SPANNUNG
    print_soll_volt[i] = dead_soll_volt_deg(soll_Deg[i], tar_volt, d12_deg, d21_deg, d22_deg, d31_deg);

    // IST-SPANNUNG
    if(rel_tick == mercy_end){
      print_ist_volt[i] = ist_end_volt - ist_start_volt;
    } else if(rel_tick == mercy_start) {
      print_ist_volt[i] = 0;
    } else {
      print_ist_volt[i] = corr_measure(print_ist_volt[i]);
      if(rel_tick == real_mid){
        ist_mid_volt = print_ist_volt[i];
      }
    }
    
    // IST-WINKEL
    if(rel_tick == real_mid){
      print_ist_deg[i] = get_deg_position() - real_mid_deg - tick_to_deg(start_tick);
    } else if(rel_tick == mercy_end){
      print_ist_deg[i] = real_mid_deg;
    } else if(rel_tick == mercy_start){
      print_ist_deg[i] = -real_mid_deg;
    } else if(rel_tick == d12_tick + offset_von_soll){
      print_ist_deg[i] = correction_movement(print_ist_volt[i], ist_start_volt, 0) - tick_to_deg(start_tick) - real_mid_deg;
      ccw_links = print_ist_deg[i];
    } else if(rel_tick == d21_tick + offset_von_soll){
      print_ist_deg[i] = correction_movement(print_ist_volt[i], ist_mid_volt, 1) - tick_to_deg(start_tick) - real_mid_deg;
      ccw_rechts = print_ist_deg[i];
    } else if(rel_tick == d22_tick + offset_von_soll){
      print_ist_deg[i] = correction_movement(print_ist_volt[i], ist_mid_volt, 0) - tick_to_deg(start_tick) - real_mid_deg;
      cw_links = print_ist_deg[i];
    } else if(rel_tick == d31_tick + offset_von_soll){
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

  drive_to(mid_tick, user_rpm);
  reached_goal(mid_tick, 2);
  dxl.ledOff(DID);
}

// ----------------- LINEARITÄT
void calc_linearity(){
  const float real_volt_per_deg = tar_volt/ges_aktiv;
  const float mid_soll_volt_real = aktiv_ccw*real_volt_per_deg;

  for(size_t i = 0; i<print_array_size ; i++){
    // LEERE ZELLEN ÜBERSPRINGEN
    if (empty_cells[i] == true) {
      print_soll_volt_real[i] = NAN;
      print_linear_real[i] = NAN;
      continue;
    }

    // SOLLSPANNUNG REAL
    print_soll_volt_real[i] = print_real_diff_mid[i] * real_volt_per_deg + mid_soll_volt_real;
    
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