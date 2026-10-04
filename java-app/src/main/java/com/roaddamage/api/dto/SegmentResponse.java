package com.roaddamage.api.dto;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;

@JsonIgnoreProperties(ignoreUnknown = true)
public class SegmentResponse {
    @JsonProperty("segment_id")
    private int segmentId;

    @JsonProperty("start_m")
    private double startM;

    @JsonProperty("end_m")
    private double endM;

    @JsonProperty("damage_index")
    private double damageIndex;

    @JsonProperty("condition")
    private String condition;

    public int getSegmentId() { return segmentId; }
    public void setSegmentId(int segmentId) { this.segmentId = segmentId; }

    public double getStartM() { return startM; }
    public void setStartM(double startM) { this.startM = startM; }

    public double getEndM() { return endM; }
    public void setEndM(double endM) { this.endM = endM; }

    public double getDamageIndex() { return damageIndex; }
    public void setDamageIndex(double damageIndex) { this.damageIndex = damageIndex; }

    public String getCondition() { return condition; }
    public void setCondition(String condition) { this.condition = condition; }
}
