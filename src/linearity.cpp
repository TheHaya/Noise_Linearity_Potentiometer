#include <Arduino.h>
#include <Dynamixel2Arduino.h>
#include <dxl_servo.h>
#include <calibrate.h>
#include <linearity.h>
#include <relay.h>

// --------------- CONSTANTS
const size_t PRINT_ARRAY_SIZE = 13;

// --------------- VARIABLES
float print_ist_deg[PRINT_ARRAY_SIZE];
float print_soll_deg[PRINT_ARRAY_SIZE];
float print_soll_volt[PRINT_ARRAY_SIZE];
float print_ist_volt[PRINT_ARRAY_SIZE];
float print_real_diff_mid[PRINT_ARRAY_SIZE];
float print_soll_volt_real[PRINT_ARRAY_SIZE];
float print_linear_real[PRINT_ARRAY_SIZE];
bool empty_cells[PRINT_ARRAY_SIZE];
bool error_lin_index[PRINT_ARRAY_SIZE];
bool error_lin, error_mech, error_midDead;

int32_t real_tick_total, soll_tick_total;
float d11_deg, d12_deg, d21_deg, d22_deg, d31_deg, d32_deg;
int32_t d11_tick, d12_tick, d21_tick, d22_tick, d31_tick, d32_tick;
float ccw_links, ccw_rechts, cw_links, cw_rechts, aktiv_ccw, aktiv_cw, ges_aktiv;
float real_mid_deg;
float lin_min, lin_max;


void lin_init(){
  real_tick_total = 0;
  soll_tick_total = 0;
  d11_tick = 0;
  d12_tick = 0;
  d21_tick = 0;
  d22_tick = 0;
  d31_tick = 0;
  d32_tick = 0;

  ccw_links = 0;
  ccw_rechts = 0;
  cw_links = 0;
  cw_rechts = 0;
  aktiv_ccw = 0;
  aktiv_cw = 0;
  ges_aktiv = 0;
  real_mid_deg = 0;

  lin_min = 100;
  lin_max = -100;

  error_lin = false;
  error_mech = false;
  error_midDead = false;
  for (size_t i = 0; i < PRINT_ARRAY_SIZE; ++i) {
    print_ist_deg[i] = 0;
    print_soll_deg[i] = 0;
    print_soll_volt[i] = 0;
    print_ist_volt[i] = 0;
    print_real_diff_mid[i] = 0;
    print_soll_volt_real[i] = 0;
    print_linear_real[i] = 0;
    empty_cells[i] = false;
    error_lin_index[i] = false;
  }
  
  // Werden eh durch Serial initialisiert
  // d11_deg = 0;
  // d12_deg = 0;
  // d21_deg = 0;
  // d22_deg = 0;
  // d31_deg = 0;
  // d32_deg = 0;
}


float lerp_dead(int32_t x, int32_t d1, int32_t d2){
  if(d1 == d2){
    return 0;
  } else {
    return (float)(x - d1) / (float)(d2 - d1);
  }
}

float dead_soll_volt_deg(float deg, float tar_volt_real,
                      float d12_deg, float d21_deg, float d22_deg, float d31_deg) {
  const float HALF = tar_volt_real * 0.5f;
  if (deg <= d12_deg) return 0.0f;
  if (deg <= d21_deg) return HALF * (deg - d12_deg) / (d21_deg - d12_deg);
  if (deg <= d22_deg) return HALF;
  if (deg <= d31_deg) return HALF + HALF * (deg - d22_deg) / (d31_deg - d22_deg);
  return tar_volt_real;
}

void linearity_movement2(){
  // 1° = 11.375 ticks
  // 1 Tick = 0.08791208791 °
  real_tick_total = end_tick - start_tick;
  soll_tick_total = deg_to_tick(target_deg_total); // ca. 330°
  float real_deg_total = tick_to_deg(real_tick_total);

  float mid_degs = 25;
  real_mid_deg = real_deg_total/2;
  float soll_mid_deg = target_deg_total/2;
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
  
  int32_t mercy_tick = 100; // 100 Ticks vor jeweiligem Ende
  int32_t mercy_start = mercy_tick;
  int32_t mercy_end = real_tick_total - mercy_tick;

  int32_t sim_tick [] = {real_mid, d21_tick, d21_tick-mid_steps, d21_tick-2*mid_steps, d21_tick-3*mid_steps, d12_tick, mercy_start,
     d22_tick, d22_tick+mid_steps, d22_tick+2*mid_steps, d22_tick+3*mid_steps, d31_tick, mercy_end
      };
  
  int32_t drive_tick[PRINT_ARRAY_SIZE];
  for(size_t i = 0; i<PRINT_ARRAY_SIZE; i++){    
    if(sim_tick[i] == real_mid){
      drive_tick[i] = sim_tick[i] + start_tick;
    }
    else if(sim_tick[i] == mercy_end || sim_tick[i] == mercy_start){
        drive_tick[i] = sim_tick[i] + start_tick;
    } else {
      drive_tick[i] = sim_tick[i] + start_tick + offset_von_soll;
    }
  }

  for (size_t i = 0; i<PRINT_ARRAY_SIZE; i++) {
    
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
    if(rel_tick == real_mid){
      print_soll_deg[i] = soll_Deg[i]-real_mid_deg;
    } else if(rel_tick == mercy_end || rel_tick == mercy_start){
       print_soll_deg[i] = soll_Deg[i]-real_mid_deg;
    } else{
       print_soll_deg[i] = soll_Deg[i]-soll_mid_deg;
    }

    // SOLL-SPANNUNG
    print_soll_volt[i] = dead_soll_volt_deg(soll_Deg[i], ist_end_volt, d12_deg, d21_deg, d22_deg, d31_deg);

    // IST-SPANNUNG
    if(rel_tick == mercy_end){
      print_ist_volt[i] = ist_start_volt;
    } else if(rel_tick == mercy_start) {
      print_ist_volt[i] = ist_end_volt;
    } else {
      print_ist_volt[i] = corr_measure();
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
      float print_deg_ccw_l = correction_movement(print_ist_volt[i], ist_end_volt, 0, 0);
      if(isnan(print_deg_ccw_l)){
        print_ist_deg[i] = NAN;
      } else{
        print_ist_deg[i] =  print_deg_ccw_l - tick_to_deg(start_tick) - real_mid_deg;
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
      print_ist_deg[i] = print_deg_ccw_r - tick_to_deg(start_tick) - real_mid_deg;
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
      print_ist_deg[i] = print_deg_cw_l - tick_to_deg(start_tick) - real_mid_deg;
      }
      // print_ist_deg[i] = print_deg_cw_l  - 180;
      cw_links = print_ist_deg[i];
      Serial.print("DEAD_CW1");
      Serial.println(cw_links);
    } else if(rel_tick == d31_tick + offset_von_soll){
      float print_deg_cw_r = correction_movement(print_ist_volt[i], ist_start_volt, 1, 1);
      if(isnan(print_deg_cw_r)){
        print_ist_deg[i] = NAN;
      } else{
      print_ist_deg[i] = print_deg_cw_r - tick_to_deg(start_tick) - real_mid_deg;
      }
      // print_ist_deg[i] = print_deg_cw_r - 180;
      cw_rechts = print_ist_deg[i];
      Serial.print("DEAD_CW2");
      Serial.println(cw_rechts);
    }
    else{
      print_ist_deg[i] = get_deg_position() - real_mid_deg - tick_to_deg(start_tick);
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

void calc_linearity2(){
  const float REAL_VOLT_PER_DEG = ist_end_volt/ges_aktiv;
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
    print_linear_real[i] = (print_ist_volt[i] - print_soll_volt_real[i])/ist_end_volt;
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

void calc_summary2(){
  float totzone = cw_links - ccw_rechts;
  aktiv_cw = fabsf(ccw_rechts - ccw_links); // gedreht wegen poti andersrum
  aktiv_ccw = fabsf(cw_links - cw_rechts);  // hier auch
  ges_aktiv = aktiv_ccw + aktiv_cw;

  Serial.print("TOTAL_ELEC");
  Serial.println(ges_aktiv);
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
void calc_errors2(){
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

