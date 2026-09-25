#include <Arduino.h>
#include <Dynamixel2Arduino.h>
#include <dxl_servo.h>
#include <calibrate.h>
#include <linearity.h>
#include <relay.h>
#include <progress.h>
#include <endless_calibrate.h>

// --------------- CONSTANTS

// --------------- VARIABLES

void endless_linearity_movement(){
  // 1° = 11.375 ticks
  // 1 Tick = 0.08791208791 °
  d11_tick = deg_to_tick(d11_deg);
  d12_tick = deg_to_tick(d12_deg);
  d21_tick = deg_to_tick(d21_deg);
  d22_tick = deg_to_tick(d22_deg);
  d31_tick = deg_to_tick(d31_deg);
  d32_tick = deg_to_tick(d32_deg);

  real_tick_total = endless_end_tick - endless_start_tick;
  soll_tick_total = deg_to_tick(target_deg_total); // ca. 330°
  float real_deg_total = tick_to_deg(real_tick_total);
  real_mid_deg = real_deg_total/2;
  float soll_mid_deg = target_deg_total/2;
  int32_t real_mid = real_tick_total/2;
  int32_t offset_von_soll = (real_tick_total-soll_tick_total) / 2;

  if(d21_tick != 0){
    mid_degs = (d21_deg - d12_deg) / 4;
  } else{
    mid_degs = (real_mid_deg - d12_deg) / 4;
  }

  if(d21_tick != 0){
    mid_steps = (d21_tick - d12_tick) / 4;
  } else{
    mid_steps = (real_mid - d12_tick) / 4;
  }
  
  for(int i = 0; i < 5; i++){ // UNBEDINGT FIXEN (maybe)
    dxl.ledOff(1);
    delay(100);
    dxl.ledOn(1);
    delay(100);
  } 

  if(d21_deg == 0){d21_deg = real_mid_deg;}
  if(d22_deg == 0){d22_deg = real_mid_deg;}
  if(d31_deg == 0){d31_deg = tick_to_deg(endless_end_tick);}
  if(d32_deg == 0){d32_deg = tick_to_deg(endless_end_tick);}
  if(d21_tick == 0){d21_tick = real_mid;}
  if(d22_tick == 0){d22_tick = real_mid;}
  if(d31_tick == 0){d31_tick = endless_end_tick;}
  if(d32_tick == 0){d32_tick = endless_end_tick;}

  float soll_Deg[] = {real_mid_deg,
     d22_deg, d22_deg+mid_degs, d22_deg+2*mid_degs, d22_deg+3*mid_degs, d31_deg, real_deg_total,
      d21_deg, d21_deg-mid_degs, d21_deg-2*mid_degs, d21_deg-3*mid_degs, d12_deg, 0};
  
  int32_t mercy_tick = 100; // 100 Ticks vor jeweiligem Ende
  int32_t mercy_start = mercy_tick;
  int32_t mercy_end = real_tick_total - mercy_tick;

  int32_t sim_tick [] = {real_mid, d21_tick, d21_tick-mid_steps, d21_tick-2*mid_steps, d21_tick-3*mid_steps, d12_tick, mercy_start,
     d22_tick, d22_tick+mid_steps, d22_tick+2*mid_steps, d22_tick+3*mid_steps, d31_tick, mercy_end
      };
  
  int32_t drive_tick[PRINT_ARRAY_SIZE];
  for(size_t i = 0; i<PRINT_ARRAY_SIZE; i++){    
    if(sim_tick[i] == real_mid){
      drive_tick[i] = sim_tick[i] + endless_start_tick;
    }
    else if(sim_tick[i] == mercy_end || sim_tick[i] == mercy_start){
        drive_tick[i] = sim_tick[i] + endless_start_tick;
    } else {
      drive_tick[i] = sim_tick[i] + endless_start_tick + offset_von_soll;
    }
  }

  for (size_t i = 0; i<PRINT_ARRAY_SIZE; i++) {
    // Ladebalken
    if(i == 0){
      report_progress("LINEAR", "D21_CHECK", 10);
    } else if(i == 2){
      report_progress("LINEAR", "D21_BETWEEN", 25);
    } else if(i == 5){
      report_progress("LINEAR", "D12_CHECK", 35);
    } else if(i == 7){
      report_progress("LINEAR", "D22_CHECK", 50);
    } else if(i == 8){
      report_progress("LINEAR", "D22_BETWEEN", 60);
    } else if(i == 11){
      report_progress("LINEAR", "D32_CHECK", 80);
    }

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
    int32_t rel_tick = tick - endless_start_tick;
    empty_cells[i] = false;
    if(rel_tick == mercy_start || rel_tick == mercy_end ||
       rel_tick == d21_tick + offset_von_soll || rel_tick == d22_tick + offset_von_soll){
        empty_cells[i] = true;
       }

    // SOLL-WINKEL
    if(rel_tick == mercy_start){
      print_soll_deg[i] = real_mid_deg;
    }
    else if(rel_tick == mercy_end){
      print_soll_deg[i] = -real_mid_deg;
    }
    else{
      print_soll_deg[i] = -tick_to_deg(rel_tick - real_mid);
    }

    // SOLL-SPANNUNG
    if(relay_switch){
      print_soll_volt[i] = dead_soll_volt_deg(soll_Deg[i], ist_start_volt, d12_deg, d21_deg, d22_deg, d31_deg);
    } else{
      print_soll_volt[i] = dead_soll_volt_deg(soll_Deg[i], ist_end_volt, d12_deg, d21_deg, d22_deg, d31_deg);
    }
    

    // IST-SPANNUNG
    if(rel_tick == mercy_end){
      if(relay_switch) {
        print_ist_volt[i] = ist_end_volt;
      } else{
        print_ist_volt[i] = ist_start_volt;
      }
      
    } else if(rel_tick == mercy_start) {
      if(relay_switch) {
        print_ist_volt[i] = ist_start_volt;
      } else{
        print_ist_volt[i] = ist_end_volt;
      }
    } else {
      print_ist_volt[i] = corr_measure();
      if(rel_tick == real_mid){
        ist_mid_volt = print_ist_volt[i];
      }
    }
    
    // IST-WINKEL
    if(rel_tick == real_mid){
      print_ist_deg[i] = get_deg_position() - real_mid_deg - tick_to_deg(endless_start_tick);
    } else if(rel_tick == mercy_end){
      print_ist_deg[i] = real_mid_deg;
    } else if(rel_tick == mercy_start){
      print_ist_deg[i] = -real_mid_deg;
    } else if(rel_tick == d12_tick + offset_von_soll){
      float print_deg_ccw_l;
      if(relay_switch){
        print_deg_ccw_l = correction_movement(print_ist_volt[i], ist_start_volt, 0, 0);
      } else {
        print_deg_ccw_l = correction_movement(print_ist_volt[i], ist_end_volt, 0, 0);
      }
      if(isnan(print_deg_ccw_l)){
        print_ist_deg[i] = NAN;
      } else{
        print_ist_deg[i] =  print_deg_ccw_l - tick_to_deg(endless_start_tick) - real_mid_deg;
      }
      // print_ist_deg[i] =  print_deg_ccw_l  - 180;
      ccw_links = print_ist_deg[i];
      Serial.print("DEAD_CCW1");
      Serial.println(ccw_links);
    } else if(rel_tick == d21_tick + offset_von_soll){
      float print_deg_ccw_r = correction_movement(print_ist_volt[i], ist_mid_volt, 1, 0);
      if(isnan(print_deg_ccw_r)){
        print_ist_deg[i] = NAN;
      } else{
      print_ist_deg[i] = print_deg_ccw_r - tick_to_deg(endless_start_tick) - real_mid_deg;
      }
      // print_ist_deg[i] = print_deg_ccw_r - 180;
      ccw_rechts = print_ist_deg[i];
      Serial.print("DEAD_CCW2");
      Serial.println(ccw_rechts);
    } else if(rel_tick == d22_tick + offset_von_soll){
      float print_deg_cw_l = correction_movement(print_ist_volt[i], ist_mid_volt, 0, 1);
      if(isnan(print_deg_cw_l)){
        print_ist_deg[i] = NAN;
      } else{
      print_ist_deg[i] = print_deg_cw_l - tick_to_deg(endless_start_tick) - real_mid_deg;
      }
      // print_ist_deg[i] = print_deg_cw_l  - 180;
      cw_links = print_ist_deg[i];
      Serial.print("DEAD_CW1");
      Serial.println(cw_links);
    } else if(rel_tick == d31_tick + offset_von_soll){
      float print_deg_cw_r;
      if(relay_switch){
        print_deg_cw_r = correction_movement(print_ist_volt[i], ist_end_volt, 1, 1);
      } else {
        print_deg_cw_r = correction_movement(print_ist_volt[i], ist_start_volt, 1, 1);
      }
      if(isnan(print_deg_cw_r)){
        print_ist_deg[i] = NAN;
      } else{
      print_ist_deg[i] = print_deg_cw_r - tick_to_deg(endless_start_tick) - real_mid_deg;
      }
      // print_ist_deg[i] = print_deg_cw_r - 180;
      cw_rechts = print_ist_deg[i];
      Serial.print("DEAD_CW2");
      Serial.println(cw_rechts);
    }
    else{
      print_ist_deg[i] = get_deg_position() - real_mid_deg - tick_to_deg(endless_start_tick);
    }
    print_ist_deg[i] = -print_ist_deg[i];
    
    // REALER WINKEL ZUR MITTE
    if(print_soll_deg[i] == 0){
      print_real_diff_mid[i] = 0;
    }
    else if(print_ist_deg[i] > 0){
      print_real_diff_mid[i] = print_ist_deg[i] + ccw_rechts;
    } else if(print_ist_deg[i] < 0){
      print_real_diff_mid[i] = print_ist_deg[i] + cw_links;
    } 
  }

  // --------------- AUSGABE ELEG_DEG

  // --------------- ERROR MITTELANZAPFUNG
  if(fabsf((cw_links + ccw_rechts) - (d21_deg + d22_deg)) > 1.5){
    error_midDead = true;
  }
  // --------------- ÜBERGABE AN PYTHON
  for (size_t i = 0; i<PRINT_ARRAY_SIZE; i++) {
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
  all_relays_off();
}

void endless_calc_linearity(){
  float REAL_VOLT_PER_DEG;
  if(relay_switch){
    REAL_VOLT_PER_DEG = ist_start_volt/ges_aktiv;
  }else{
    REAL_VOLT_PER_DEG = ist_end_volt/ges_aktiv;
  }
  
  const float MID_SOLL_VOLT_REAL = aktiv_ccw*REAL_VOLT_PER_DEG;

  for(size_t i = 0; i<PRINT_ARRAY_SIZE ; i++){
    // LEERE ZELLEN ÜBERSPRINGEN
    if (empty_cells[i] == true) {
      print_soll_volt_real[i] = NAN;
      print_linear_real[i] = NAN;
      continue;
    }

    // SOLLSPANNUNG REAL
    print_soll_volt_real[i] = print_real_diff_mid[i] * REAL_VOLT_PER_DEG + MID_SOLL_VOLT_REAL;
    
    // LINEARITÄT
    if(relay_switch){
      print_linear_real[i] = (print_ist_volt[i] - print_soll_volt_real[i])/ist_start_volt;
    }else{
      print_linear_real[i] = (print_ist_volt[i] - print_soll_volt_real[i])/ist_end_volt;
    }
    
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
  
  for(size_t i = 0; i<PRINT_ARRAY_SIZE ; i++){
    Serial.print("RESULT;");
    Serial.print("idx:");   
    Serial.print(i);
    Serial.print(";Soll-Spannung Real:");   
    Serial.print(print_soll_volt_real[i], 3);
    Serial.print(";Linearität:"); 
    Serial.println(print_linear_real[i], 6);
  }
}

void endless_calc_summary(){
  float totzone = cw_links - ccw_rechts;
  aktiv_cw = fabsf(ccw_rechts - ccw_links); // gedreht wegen poti andersrum
  aktiv_ccw = fabsf(cw_links - cw_rechts);  // hier auch
  ges_aktiv = aktiv_ccw + aktiv_cw;

  Serial.print("TOTAL_ELEC");
  Serial.println(ges_aktiv+totzone);
  Serial.print("SUMMARY;");
  Serial.print("Totzone:");   
  Serial.print(totzone, 1);
  Serial.print(";AktivCW:"); 
  Serial.print(aktiv_cw, 1);
  Serial.print(";AktivCCW:");
  Serial.print(aktiv_ccw, 1);
  Serial.print(";AktivSumme:");
  Serial.println(ges_aktiv, 1);
}

// ERROR AUSGABE EXCEL
void endless_calc_errors(){
  Serial.print("ERROR_LIN;");
  Serial.print("IDX:");
  bool first = true;
  if (error_lin == true) {
    for (size_t i = 0; i < PRINT_ARRAY_SIZE; i++) {
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
  }
  Serial.print(";LIN_MAX:");
  Serial.print(lin_max, 6);
  Serial.print(";LIN_MIN:");
  Serial.println(lin_min, 6);
}

