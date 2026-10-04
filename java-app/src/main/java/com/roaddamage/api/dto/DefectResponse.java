package com.roaddamage.api.dto;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;

@JsonIgnoreProperties(ignoreUnknown = true)
public class DefectResponse {
    @JsonProperty("defect_id")
    private int defectId;

    @JsonProperty("class")
    private String defectClass;

    @JsonProperty("lat")
    private double lat;

    @JsonProperty("lon")
    private double lon;

    @JsonProperty("severity")
    private String severity;

    @JsonProperty("priority")
    private Double priority;

    @JsonProperty("estimated_cost")
    private Double estimatedCost;

    @JsonProperty("status")
    private String status;

    @JsonProperty("crop_path")
    private String cropPath;
    
    @JsonProperty("recurrence")
    private boolean recurrence;

    public int getDefectId() { return defectId; }
    public void setDefectId(int defectId) { this.defectId = defectId; }

    public String getDefectClass() { return defectClass; }
    public void setDefectClass(String defectClass) { this.defectClass = defectClass; }

    public double getLat() { return lat; }
    public void setLat(double lat) { this.lat = lat; }

    public double getLon() { return lon; }
    public void setLon(double lon) { this.lon = lon; }

    public String getSeverity() { return severity; }
    public void setSeverity(String severity) { this.severity = severity; }

    public Double getPriority() { return priority; }
    public void setPriority(Double priority) { this.priority = priority; }

    public Double getEstimatedCost() { return estimatedCost; }
    public void setEstimatedCost(Double estimatedCost) { this.estimatedCost = estimatedCost; }

    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }

    public String getCropPath() { return cropPath; }
    public void setCropPath(String cropPath) { this.cropPath = cropPath; }

    public boolean isRecurrence() { return recurrence; }
    public void setRecurrence(boolean recurrence) { this.recurrence = recurrence; }
}
