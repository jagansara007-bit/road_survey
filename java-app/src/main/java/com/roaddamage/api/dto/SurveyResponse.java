package com.roaddamage.api.dto;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;

@JsonIgnoreProperties(ignoreUnknown = true)
public class SurveyResponse {
    @JsonProperty("survey_id")
    private int surveyId;

    @JsonProperty("route_name")
    private String routeName;

    @JsonProperty("surveyed_on")
    private String surveyedOn;

    @JsonProperty("status")
    private String status;

    public int getSurveyId() { return surveyId; }
    public void setSurveyId(int surveyId) { this.surveyId = surveyId; }

    public String getRouteName() { return routeName; }
    public void setRouteName(String routeName) { this.routeName = routeName; }

    public String getSurveyedOn() { return surveyedOn; }
    public void setSurveyedOn(String surveyedOn) { this.surveyedOn = surveyedOn; }

    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }
}
