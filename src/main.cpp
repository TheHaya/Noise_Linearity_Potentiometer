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

// --------------- CONSTANTS
const int BUTTON = 19;


// --------------- VARIABLES
bool linear_checked;
elapsedMillis but_millis;
int but_timer = 200;
bool but_up = HIGH;
bool but_press;
int counter_mode;

// --------------- SETUP AND ASSIST FUNCTIONS
void setup(){
  Serial.begin(115200);
  dxl.begin(DXL_BAUD);
  dxl.setPortProtocolVersion(DXL_PROTOCOL);

  dxl.torqueOff(DID);
  dxl.setOperatingMode(DID, OP_EXTENDED_POSITION);
  dxl.writeControlTableItem(DRIVE_MODE, DID, 0b101);
  dxl.writeControlTableItem(HOMING_OFFSET, DID, 0);
  dxl.writeControlTableItem(PROFILE_VELOCITY, DID, 1000);
  dxl.writeControlTableItem(PROFILE_ACCELERATION, DID, 500);
  dxl.torqueOn(DID);
  dxl.ledOn(DID);
  relays_init();
  all_relays_off();
  pinMode(BUTTON, INPUT_PULLUP);

}


// --------------- LOOP
void loop(){
  but_press = digitalRead(BUTTON);
  if(but_press == LOW && but_up == HIGH && but_millis > but_timer){
    Serial.println("BUTTON");
    but_millis = 0;
  }
  but_up = but_press;

  if(Serial.available()){
    String command = Serial.readStringUntil('\n');
    command.trim();

    // EINGABE VON PYTHON
    if(command.startsWith("SETV:")){tar_volt = command.substring(5).toFloat();}
    if(command.startsWith("SETW:")){target_deg_total = command.substring(5).toFloat();}
    if(command.startsWith("SETS:")){user_rpm = command.substring(5).toFloat();}
    if(command.startsWith("goto:")){user_go_to = command.substring(5).toFloat();}
    if(command.startsWith("dead11:")){d11_deg = command.substring(7).toFloat();}
    if(command.startsWith("dead12:")){d12_deg = command.substring(7).toFloat();}
    if(command.startsWith("dead21:")){d21_deg = command.substring(7).toFloat();}
    if(command.startsWith("dead22:")){d22_deg = command.substring(7).toFloat();}
    if(command.startsWith("dead31:")){d31_deg = command.substring(7).toFloat();}
    if(command.startsWith("dead32:")){d32_deg = command.substring(7).toFloat();}

    if(command == "ZERO"){
      go_zero();
    }
  
    if(command == "INIT_GO"){
      bool linear_checked = false;

      dxl_init();
      calibrate_currents();
      //Serial.println("CANCEL");
      check_ends(false); // >>>>>>>>>>>>>>>>>>>>>> ÄNDERN- NUR MIT DMM = TRUE
      if(cancelled == true){
        Serial.println("CANCEL");
        cancelled = false;
      }
      drive_to(ZERO_TICK, user_rpm);
      reached_goal(ZERO_TICK, 2);
    }

    if(command == "NOISE_GO"){
      apply_relay_mode(NOISE_RELAY_MODE);
      if(cancelled == false){
        drive_to(sim_mercy_end, user_rpm/2);
        reached_goal(sim_mercy_end, 1);
        Serial.println("NOISE_READY");
      } else{
        Serial.println("CANCEL");
        cancelled = false;
      }
    }
    if(command == "NOISE_START"){
      noise_movement();
      if(cancelled == true){
        Serial.println("CANCEL");
        cancelled = false;
      }
      drive_to(ZERO_TICK, user_rpm);
      reached_goal(ZERO_TICK, 2);
      dxl.ledOff(DID);
      Serial.println("NOISE_FINISH");
    }

    if(command == "LINEAR_GO"){
      //linear_checked = true;
      apply_relay_mode(LINEARITY_RELAY_MODE);
      if(cancelled == false){
        Serial.println("LINEAR_READY");
      } else{
        Serial.println("CANCEL");
        cancelled = false;
      }
    }
    if(command == "LINEAR_START"){
      lin_init();
      linearity_movement();
      calc_summary();
      calc_linearity();
      calc_errors();
      if(cancelled == true){
        Serial.println("CANCEL");
        cancelled = false;
      }
      drive_to(ZERO_TICK, user_rpm);
      reached_goal(ZERO_TICK, 2);
      dxl.ledOff(DID);
      Serial.println("LINEAR_FINISH");
    }

    if(linear_checked == false){ // Falls elec_deg und linear beide angekreuzt wurden dann einfach elec_deg ignorieren
      if(command == "ELEC_DEG_GO"){
        apply_relay_mode(ELEC_DEG_RELAY_MODE);
        if(cancelled == false){
          Serial.println("ELEC_DEG_READY");
        } else{
          Serial.println("CANCEL");
          cancelled = false;
        }
      }
      if(command == "ELEC_DEG_START"){
        elec_deg_movement();
        if(cancelled == true){
          Serial.println("CANCEL");
          cancelled = false;
        }
        drive_to(ZERO_TICK, user_rpm);
        reached_goal(ZERO_TICK, 2);
        dxl.ledOff(DID);
        Serial.println("ELEC_DEG_FINISH");
      }
    }
    /*
    if(command =="SWITCH"){
      switch(counter_mode){
        case 0:
          apply_relay_mode(0);
          counter_mode++;
          break;
        case 1:
          apply_relay_mode(1);
          counter_mode++;
          break;
        case 2:
          apply_relay_mode(2);
          counter_mode++;
          break;
        case 3:
          apply_relay_mode(4);
          counter_mode++;
          break;
        case 4:
          apply_relay_mode(8);
          counter_mode++;
          break;
        case 5:
          apply_relay_mode(16);
          counter_mode++;
          break;
        case 6:
          apply_relay_mode(32);
          counter_mode++;
          break;
        case 7:
          apply_relay_mode(64);
          counter_mode++;
          break;
        case 8:
          apply_relay_mode(128);
          counter_mode++;
          break;
        case 9:
          apply_relay_mode(256);
          counter_mode++;
          break;
        case 10:
          apply_relay_mode(512);
          counter_mode=0;
          break;
        default:
          break;
      }
    }*/
  }
}
