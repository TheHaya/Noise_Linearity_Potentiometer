#include <Arduino.h>

void report_progress(const char* mode, const char* phase, uint8_t percent){
    if(percent > 100){
        percent = 100;
    }

    Serial.print("PROGRESS;");
    Serial.print(mode);
    Serial.print(";");
    Serial.print(percent);
    Serial.print(";");
    Serial.println(phase);
}