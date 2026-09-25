#include <Arduino.h>
#include <Dynamixel2Arduino.h>
#include <math.h>
#include <elapsedMillis.h>

#include <dxl_servo.h>
#include <calibrate.h>
#include <noise.h>
#include <linearity.h>
#include <elec_deg.h>
#include <relay.h>
#include <side_functions.h>
#include <endless_calibrate.h>
#include <endless_elec_deg.h>
#include <endless_noise.h>
#include <progress.h>
#include <endless_linearity.h>

// --------------- CONSTANTS
const int BUTTON = 19;
const int BUT_TIMER = 200;
const int LED_R = 18;
const int LED_Y = 17;
const int LED_G = 16;
const int BUZZER = 14;

// --------------- VARIABLES
const int POLLING_TIMER_PING = 200;
bool linear_checked;
elapsedMillis but_millis;
elapsedMillis servo_ping_timer;
bool measurement_active = false;
bool servo_online = false;
bool but_up = HIGH;
bool but_press;
bool endless_poti;
// bool calib_finished;
bool ping_ok;

// --------------- SETUP AND ASSIST FUNCTIONS

void setLEDS(int setting){
  switch(setting){
    case 0:
    digitalWrite(LED_R, LOW);
    digitalWrite(LED_Y, LOW);
    digitalWrite(LED_G, LOW);
    break;
    case 1:
    digitalWrite(LED_R, HIGH);
    digitalWrite(LED_Y, LOW);
    digitalWrite(LED_G, LOW);
    break;
    case 2:
    digitalWrite(LED_R, LOW);
    digitalWrite(LED_Y, HIGH);
    digitalWrite(LED_G, LOW);
    break;
    case 3:
    digitalWrite(LED_R, LOW);
    digitalWrite(LED_Y, LOW);
    digitalWrite(LED_G, HIGH);
    break;
    default:
    digitalWrite(LED_R, LOW);
    digitalWrite(LED_Y, LOW);
    digitalWrite(LED_G, HIGH);
    break;
  }
}

void measurements_init(){
  setLEDS(1);
  endless_poti = false;
  linear_checked = false;
  // calib_finished = false;
  dxl_init();
  calibrate_init();
  endless_init();
  endless_noise_init();
  elec_deg_init();
  lin_init();
  
}

bool check_init_value(bool condition, const char* variable_name){
  if(condition){
    return true;
  }

  Serial.print("INIT_CHECK_FAIL:");
  Serial.println(variable_name);
  return false;
}

bool check_measurements_init(){
  bool ok = true;

  // main.cpp
  ok &= check_init_value(endless_poti == false, "endless_poti");
  ok &= check_init_value(linear_checked == false, "linear_checked");

  // dxl_init()
  ok &= check_init_value(cancelled == false, "cancelled");
  ok &= check_init_value(stopped_tick == 0, "stopped_tick");

  ok &= check_init_value(cal_cur0 == 0.0f, "cal_cur0");
  ok &= check_init_value(cal_cur1 == 0.0f, "cal_cur1");
  ok &= check_init_value(cal_cur2 == 0.0f, "cal_cur2");
  ok &= check_init_value(cal_cur3 == 0.0f, "cal_cur3");

  ok &= check_init_value(cur_pos == 0, "cur_pos");
  ok &= check_init_value(cur_cur == 0.0f, "cur_cur");

  ok &= check_init_value(rpm1 == 0.0f, "rpm1");
  ok &= check_init_value(rpm2 == 0.0f, "rpm2");
  ok &= check_init_value(rpm3 == 0.0f, "rpm3");

  // calibrate_init()
  ok &= check_init_value(start_tick == 0, "start_tick");
  ok &= check_init_value(end_tick == 0, "end_tick");
  ok &= check_init_value(real_mid_tick == 0, "real_mid_tick");
  ok &= check_init_value(sim_mercy_start == 0, "sim_mercy_start");
  ok &= check_init_value(sim_mercy_end == 0, "sim_mercy_end");

  ok &= check_init_value(ist_start_volt == 0.0f, "ist_start_volt");
  ok &= check_init_value(ist_end_volt == 0.0f, "ist_end_volt");
  ok &= check_init_value(ist_mid_volt == 0.0f, "ist_mid_volt");

  ok &= check_init_value(real_time1 == 0.0f, "real_time1");
  ok &= check_init_value(real_time2 == 0.0f, "real_time2");
  ok &= check_init_value(real_time3 == 0.0f, "real_time3");

  ok &= check_init_value(theo_time1 == 0.0f, "theo_time1");
  ok &= check_init_value(theo_time2 == 0.0f, "theo_time2");
  ok &= check_init_value(theo_time3 == 0.0f, "theo_time3");

  ok &= check_init_value(delay1 == 0.0f, "delay1");
  ok &= check_init_value(delay2 == 0.0f, "delay2");
  ok &= check_init_value(delay3 == 0.0f, "delay3");

  // endless_init()
  ok &= check_init_value(endless_start_volt == 0.0f, "endless_start_volt");
  ok &= check_init_value(endless_end_volt == 0.0f, "endless_end_volt");
  ok &= check_init_value(endless_start_tick == 0.0f, "endless_start_tick");
  ok &= check_init_value(endless_end_tick == 0.0f, "endless_end_tick");
  ok &= check_init_value(endless_sim_start == 0, "endless_sim_start");
  ok &= check_init_value(endless_sim_end == 0, "endless_sim_end");

  // endless_noise_init()
  ok &= check_init_value(
      endless_noise_prep_start == 0.0f,
      "endless_noise_prep_start"
  );

  ok &= check_init_value(
      endless_noise_prep_end == 0.0f,
      "endless_noise_prep_end"
  );

  // elec_deg_init()
  ok &= check_init_value(smaller_steps == false, "smaller_steps");

  for(size_t i = 0; i < ELEC_ARRAY_SIZE; i++){
    ok &= check_init_value(
        print_elec_deg[i] == 0.0f,
        "print_elec_deg"
    );

    ok &= check_init_value(
        print_elec_volt[i] == 0.0f,
        "print_elec_volt"
    );
  }

  // lin_init()
  ok &= check_init_value(real_tick_total == 0, "real_tick_total");
  ok &= check_init_value(soll_tick_total == 0, "soll_tick_total");

  ok &= check_init_value(error_lin == false, "error_lin");
  ok &= check_init_value(error_mech == false, "error_mech");
  ok &= check_init_value(error_midDead == false, "error_midDead");

  // Diese beiden haben absichtlich keine Nullwerte:
  ok &= check_init_value(lin_min == 100.0f, "lin_min");
  ok &= check_init_value(lin_max == -100.0f, "lin_max");

  for(size_t i = 0; i < PRINT_ARRAY_SIZE; i++){
    ok &= check_init_value(print_ist_deg[i] == 0.0f, "print_ist_deg");
    ok &= check_init_value(print_soll_deg[i] == 0.0f, "print_soll_deg");
    ok &= check_init_value(print_soll_volt[i] == 0.0f, "print_soll_volt");
    ok &= check_init_value(print_ist_volt[i] == 0.0f, "print_ist_volt");
    ok &= check_init_value(empty_cells[i] == false, "empty_cells");
    ok &= check_init_value(error_lin_index[i] == false, "error_lin_index");
  }

  return ok;
}


bool abort_if_cancelled(){
  if(!cancelled) return false;
  stop_motion();
  Serial.println("CANCEL");
  if(ping_ok){
    setLEDS(3);
  }
  all_relays_off();
  uint8_t error_code = 0;
  bool read_ok = read_hardware_error_status(error_code, DID);

  if (!read_ok) {
    Serial.println("HARDWARE_ERROR_STATUS konnte nicht gelesen werden");
  } else if (error_code != 0) {
    Serial.print("DXL HW Error: ");
    Serial.println(error_code, BIN);
  }
  return true;
}

bool initialize_dxl_safely()
{
    if (!dxl.ping(DID)) {
        Serial.println("DXL_INIT_ERROR: PING");
        return false;
    }

    if (!dxl.torqueOff(DID)) {
        Serial.println("DXL_INIT_ERROR: TORQUE_OFF");
        return false;
    }

    if (!dxl.setOperatingMode(DID, OP_EXTENDED_POSITION)) {
        Serial.println("DXL_INIT_ERROR: OPERATING_MODE");
        return false;
    }

    if (!dxl.writeControlTableItem(DRIVE_MODE, DID, 0b101) ||
        !dxl.writeControlTableItem(HOMING_OFFSET, DID, 0) ||
        !dxl.writeControlTableItem(PROFILE_VELOCITY, DID, 1000) ||
        !dxl.writeControlTableItem(CURRENT_LIMIT, DID, 900) ||
        !dxl.writeControlTableItem(PROFILE_ACCELERATION, DID, 500)) {
        Serial.println("DXL_INIT_ERROR: CONFIG");
        return false;
    }

    float raw_position =
        dxl.getPresentPosition(DID, UNIT_RAW);

    if (dxl.getLastLibErrCode() != DXL_LIB_OK ||
        !isfinite(raw_position)) {
        Serial.println("DXL_INIT_ERROR: PRESENT_POSITION");
        return false;
    }

    int32_t present_position = lroundf(raw_position);

    if (!dxl.setGoalPosition(DID, present_position, UNIT_RAW)) {
        Serial.println("DXL_INIT_ERROR: HOLD_POSITION");
        return false;
    }

    if (!dxl.torqueOn(DID)) {
        Serial.println("DXL_INIT_ERROR: TORQUE_ON");
        return false;
    }

    Serial.print("DXL_INIT_OK: HOLD=");
    Serial.println(present_position);
    return true;
}

void setup(){
  Serial.begin(115200);
  bool dxl_ready = false;
  dxl.begin(DXL_BAUD);
  dxl.setPortProtocolVersion(DXL_PROTOCOL);

  dxl.torqueOff(DID);
  dxl.setOperatingMode(DID, OP_EXTENDED_POSITION);
  dxl.writeControlTableItem(DRIVE_MODE, DID, 0b101);
  dxl.writeControlTableItem(HOMING_OFFSET, DID, 0);
  dxl.writeControlTableItem(PROFILE_VELOCITY, DID, 1000);
  dxl.writeControlTableItem(CURRENT_LIMIT, DID, 900);
  dxl.writeControlTableItem(PROFILE_ACCELERATION, DID, 500);
  dxl.torqueOn(DID);
  dxl.ledOn(DID);
  relays_init();
  all_relays_off();
  pinMode(BUTTON, INPUT_PULLUP);
  pinMode(LED_R, OUTPUT);
  pinMode(LED_Y, OUTPUT);
  pinMode(LED_G, OUTPUT);
  pinMode(BUZZER, OUTPUT);
  digitalWrite(BUZZER, LOW);

  // dxl_ready = initialize_dxl_safely();

  // if (!dxl_ready) {
  //   dxl.torqueOff(DID);
  //   setLEDS(1); // Fehleranzeige
// }
}

// --------------- LOOP
void loop(){
  if(servo_ping_timer > POLLING_TIMER_PING){
    servo_ping_timer = 0;

    ping_ok = dxl.ping(DID);

    if(ping_ok && !servo_online){
      servo_online = true;

      if(!measurement_active){
        setLEDS(3);
      }
    }
    else if(!ping_ok && servo_online){
      servo_online = false;

      if(!measurement_active){
        setLEDS(0);
      }
    }
  }


  but_press = digitalRead(BUTTON);
  if(but_press == LOW && but_up == HIGH && but_millis > BUT_TIMER){
    Serial.println("BUTTON");
    but_millis = 0;
  }
  but_up = but_press;

  if(Serial.available()){
    String command = Serial.readStringUntil('\n');
    command.trim();

    if(command == "STOP"){
      cancelled = true;
      abort_if_cancelled();
      return;
    }

    // EINGABE VON PYTHON
    if(command.startsWith("SETV:")){tar_volt = command.substring(5).toFloat();}
    if(command.startsWith("SETW:")){target_deg_total = command.substring(5).toFloat();}
    if(command.startsWith("SETS:")){user_rpm = command.substring(5).toFloat();}
    if(command.startsWith("REL_SW:")){relay_switch = command.substring(7).toInt();}
    if(command.startsWith("hohlwelle:")){hohlwelle = command.substring(10).toInt();}
    if(command.startsWith("goto:")){user_go_to = command.substring(5).toFloat();}
    if(command.startsWith("dead11:")){d11_deg = command.substring(7).toFloat();}
    if(command.startsWith("dead12:")){d12_deg = command.substring(7).toFloat();}
    if(command.startsWith("dead21:")){d21_deg = command.substring(7).toFloat();}
    if(command.startsWith("dead22:")){d22_deg = command.substring(7).toFloat();}
    if(command.startsWith("dead31:")){d31_deg = command.substring(7).toFloat();}
    if(command.startsWith("dead32:")){d32_deg = command.substring(7).toFloat();}
    if(command.startsWith("RES_I:")){measure_start_resistance = command.substring(6).toInt();}
    if(command.startsWith("RES_F:")){measure_end_resistance = command.substring(6).toInt();}
    if(command.startsWith("RES_T:")){measure_total_resistance = command.substring(6).toInt();}
    if(command == "INIT_GO"){
      measurement_active = true;
      report_progress("MECH", "INIT_GO", 0);
      measurements_init();

      if(!check_measurements_init()){
        cancelled = true;
        dxl.torqueOff(DID);
        all_relays_off();
        Serial.println("INIT_CHECK_FAILED");
        return;
      }

      relays_init();
      calc_rpm();
      if(target_deg_total == 360){
        endless_poti = true;
      } 
      Serial.println("INIT_FINISH");
    }
    
    if(command == "CALIB_GO"){
      if(endless_poti){
        if(relay_switch == 0){
          apply_relay_mode(INIT_RELAY_MODE);
        } else {
          apply_relay_mode(POL_INIT_RELAY_MODE);
        }
        delay(1000);
        report_progress("MECH", "CALIBRATE_CURRENTS", 40);
        if(!calibrate_currents()){
          Serial.println("CALIBRATE_CURRENTS_FAILED");
          cancelled = true;
          abort_if_cancelled();
          return;
        }
        report_progress("MECH", "ENDLESS_VOLT_CROSSOVER", 60);
        find_endless_volt_crossover();
        // report_progress in der Funktion 
        find_endless_starting_point();
        // calib_finished = true;
      }
      else{
        if(relay_switch == 0){
          apply_relay_mode(INIT_RELAY_MODE);
        } else {
          apply_relay_mode(POL_INIT_RELAY_MODE);
        }
        delay(1000);
        report_progress("MECH", "CHECK_BEGINNING", 20);
        check_beginning(target_deg_total);
        if(abort_if_cancelled()) return;

        report_progress("MECH", "CALIBRATE_CURRENTS", 40);
        if(!calibrate_currents()){
          cancelled = true;
          abort_if_cancelled();
          return;
        }
        
        // report_progress ist in check_ends()
        check_ends();
        if(abort_if_cancelled()) return; //  ÄNDERN: NUR MIT DMM = TRUE
      }
      drive_to(beginning_tick, user_rpm);
      reached_goal(beginning_tick, 2);
      report_progress("MECH", "FINISH_CHECK_ENDS", 100);
      // drive_and_check(ZERO_TICK, user_rpm);
      // drive_and_check(beginning_tick, user_rpm);
      Serial.println("CALIB_FINISH");
    }

    if(command == "NOISE_GO"){
      report_progress("NOISE", "NOISE_GO", 0);
      if(relay_switch == 0){
          apply_relay_mode(NOISE_RELAY_MODE);
        } else {
          apply_relay_mode(POL_NOISE_RELAY_MODE);
        }
      // if(endless_poti){
      //   endless_noise_preparation_movement();
        
      //   drive_to(endless_sim_start, user_rpm);
      //   reached_goal(endless_sim_start, 2, 0, 15000);  
      // }
      // else{
        drive_to(sim_mercy_start, user_rpm);
        reached_goal(sim_mercy_start, 2, 1);
        report_progress("NOISE", "NOISE_WAIT", 40);
        noise_preparation_movement();
        // if(cancelled == false){
        drive_to(sim_mercy_end, user_rpm);
        reached_goal(sim_mercy_end, 2, 0, 15000);
        
        // drive_and_check(sim_mercy_end, user_rpm, 0);

        // }
      if(cancelled == false){
        Serial.println("NOISE_READY");
      } else{
        Serial.println("CANCEL");
        return;
        // cancelled = false;
      }
      
    }
    if(command == "NOISE_START"){
      report_progress("NOISE", "NOISE_MOVEMENT", 50);
      // if(endless_poti){
      //   endless_noise_movement();
      // } else{
        noise_movement(); 
      // }
      if(cancelled == true){
        Serial.println("CANCEL");
        return;
        // cancelled = false;
      }
      // drive_to(ZERO_TICK, user_rpm);
      // reached_goal(ZERO_TICK, 2);
      // all_relays_off();
      // dxl.ledOff(DID);
      report_progress("NOISE", "NOISE_FINISH", 100);
      Serial.println("NOISE_FINISH");
    }

    if(command == "LINEAR_GO"){
      report_progress("LINEAR", "LINEAR_GO", 0);
      linear_checked = true; if(abort_if_cancelled()) return;
      if(relay_switch == 0){
          apply_relay_mode(LINEARITY_RELAY_MODE);
        } else {
          apply_relay_mode(POL_LINEARITY_RELAY_MODE);
        }
      if(cancelled == false){
        Serial.println("LINEAR_READY");
      } else{
        Serial.println("CANCEL");
        return;
        // cancelled = false;
      }
    }
    if(command == "LINEAR_START"){
      report_progress("LINEAR", "LINEAR_START", 0);
      if(endless_poti){
        endless_linearity_movement(); if(abort_if_cancelled()) return;
        report_progress("LINEAR", "CALC_SUMMARY", 80);
        endless_calc_summary();
        endless_calc_linearity();
        endless_calc_errors();
        if(cancelled == true){
          Serial.println("CANCEL");
          return;
          // cancelled = false;
        }
      } else{
        linearity_movement2(); if(abort_if_cancelled()) return;
        report_progress("LINEAR", "CALC_SUMMARY", 80);
        calc_summary2();
        calc_linearity2();
        calc_errors2();
        if(cancelled == true){
          Serial.println("CANCEL");
          return;
          // cancelled = false;
        }
      }
      
      // drive_to(ZERO_TICK, user_rpm);
      // reached_goal(ZERO_TICK, 2);
      // dxl.ledOff(DID);
      report_progress("LINEAR", "LINEAR_FINISH", 100);
      Serial.println("LINEAR_FINISH");
    }

    if(linear_checked == false){ // Falls elec_deg und linear beide angekreuzt wurden dann einfach elec_deg ignorieren
      if(command == "ELEC_DEG_GO"){
        report_progress("ELEC", "ELEC_GO", 0);
        if(abort_if_cancelled()) return;
        if(relay_switch == 0){
          apply_relay_mode(ELEC_DEG_RELAY_MODE);
        } else {
          apply_relay_mode(POL_ELEC_DEG_RELAY_MODE);
        }
        if(cancelled == false){
          Serial.println("ELEC_DEG_READY");
        } else{
          Serial.println("CANCEL");
          return;
          // cancelled = false;
        }
      }
      if(command == "ELEC_DEG_START"){
        if(endless_poti){
          endless_elec_deg_movement();
        } else{
          elec_deg_movement();
        }
        if(cancelled == true){
          Serial.println("CANCEL");
          return;
          //cancelled = false;
        }
        // drive_to(ZERO_TICK, user_rpm);
        // reached_goal(ZERO_TICK, 2);
        // dxl.ledOff(DID);
        report_progress("ELEC", "ELEC_FINISH", 100);
        Serial.println("ELEC_DEG_FINISH");
      }
    }

    if(command == "ALL_END"){
      cancelled = false;
      drive_to(beginning_tick, user_rpm);
      reached_goal(beginning_tick, 2);
      // drive_and_check(ZERO_TICK, user_rpm);
      // drive_and_check(beginning_tick, user_rpm);

      all_relays_off();
      dxl.ledOff(DID);
      measurement_active = false;
      setLEDS(3);
      linear_checked = false;
    }

    if(command == "NOISE_END"){
      cancelled = false;
      drive_to(beginning_tick, user_rpm);
      reached_goal(beginning_tick, 2);
      // drive_and_check(ZERO_TICK, user_rpm);
      // drive_and_check(beginning_tick, user_rpm);
      all_relays_off();
      dxl.ledOff(DID);
      measurement_active = false;
      setLEDS(2);
      linear_checked = false;
    }
    

    if(command == "LIN_END"){
      cancelled = false;
      drive_to(beginning_tick, user_rpm);
      reached_goal(beginning_tick, 2);
      // drive_and_check(ZERO_TICK, user_rpm);
      // drive_and_check(beginning_tick, user_rpm);
      all_relays_off();
      dxl.ledOff(DID);
      measurement_active = false;
      setLEDS(2);
      linear_checked = false;
    }

    if(command == "FAULT_LED"){
      setLEDS(2);
    }

    if(command == "ZERO"){
      measurements_init();
      go_zero();
      setLEDS(3);
    } 

    if(command == "GOTO"){
      measurements_init();
      go_to();
      setLEDS(3);
    } 

    if(command == "WHERE"){
      measurements_init();
      show_cur_pos();
      setLEDS(3);
    }

    if(command == "REL_TESTER"){
      rel_tester();
    }
    
    if(command == "TESTER"){
    }
  }
}
