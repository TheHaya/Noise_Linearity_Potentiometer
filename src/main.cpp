#include <Arduino.h>
#include <Dynamixel2Arduino.h>
#include <math.h>
#include <elapsedMillis.h>

#include <servo.h>
#include <calibrate.h>
#include <noise.h>
#include <linearity.h>
#include <elec_deg.h>


// --------------- CONSTANTS
const int BUTTON = 12;


// --------------- VARIABLES
bool linear_checked;
elapsedMillis but_millis;
uint but_timer = 200;
bool but_up = HIGH;
bool but_press;

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
    /*
    if(command == "ENDS"){
      modes.push_back(1);
    }
    if(command == "ELEC"){
      modes.push_back(2);
    }
    if(command == "NOISE"){
      modes.push_back(3);
    }
    if(command == "LINEAR"){
      modes.push_back(4);
    }*/

    if(command == "INIT_GO"){
      bool linear_checked = false;

      dxl_init();
      calibrate_currents();
      //Serial.println("CANCEL");
      check_ends(true); // >>>>>>>>>>>>>>>>>>>>>> ÄNDERN- NUR MIT DMM = TRUE
      if(cancelled == true){
        Serial.println("CANCEL");
        cancelled = false;
      }
    }

    if(command == "NOISE_GO"){
      if(cancelled == false){
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
      linear_checked = true;

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
    if(command == "START"){
      if(modes.size() > 0){
        for(int i = 0; i < modes.size(); i++){
          switch(modes[i]){
            case 1:
                
                Serial.println("ENDS_FINISH");
                break;
                
            case 2:
              elec_deg_movement();
              break;
            case 3:
              noise_movement();
              break;
            case 4:
              linearity_movement();
              break;
            default:
              break;
          }
          if(cancelled == true){
          Serial.println("CANCEL");
          cancelled = false;
          }
        }
      }   
      drive_to(ZERO_TICK, user_rpm);
      reached_goal(ZERO_TICK, 2);
      dxl.ledOff(DID);
      Serial.println("FINISH");
    }*/



    /*
    if(command == "ENDS_GO"){
      dxl_init();
      calibrate_currents();
      check_ends();
      
      if(cancelled == true){
        Serial.println("CANCEL");
        cancelled = false;
      }
      drive_to(ZERO_TICK, user_rpm);
      reached_goal(ZERO_TICK, 2);
      dxl.ledOff(DID);
      Serial.println("ENDS_FINISH");
    }

     if(command == "ELEC_DEG_GO"){
      dxl_init();
      calibrate_currents();
      check_ends(true);
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

    if(command == "NOISE_GO"){
      dxl_init();
      calibrate_currents();
      check_ends();
      
      if(cancelled == false){
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
      dxl_init();
      lin_init();
      calibrate_currents();
      check_ends(true);
      
      if(cancelled == false){
        Serial.println("LINEAR_READY");
      } else{
        Serial.println("CANCEL");
        cancelled = false;
      }
    }
    if(command == "LINEAR_START"){
      linearity_movement();

      if(cancelled == true){
        Serial.println("CANCEL");
        cancelled = false;
      }
      drive_to(ZERO_TICK, user_rpm);
      reached_goal(ZERO_TICK, 2);
      dxl.ledOff(DID);
      Serial.println("LINEAR_FINISH");
    }*/
  }
}
