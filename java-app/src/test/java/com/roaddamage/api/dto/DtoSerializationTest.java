package com.roaddamage.api.dto;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

public class DtoSerializationTest {

    private final ObjectMapper mapper = new ObjectMapper();

    @Test
    public void testSurveyResponseDeserialization() throws Exception {
        String json = """
        {
            "survey_id": 42,
            "route_name": "NH-44 Expressway",
            "surveyed_on": "2026-10-05",
            "status": "completed",
            "source": "video_random_hash.mp4"
        }
        """;
        SurveyResponse res = mapper.readValue(json, SurveyResponse.class);
        assertEquals(42, res.getSurveyId());
        assertEquals("NH-44 Expressway", res.getRouteName());
        assertEquals("2026-10-05", res.getSurveyedOn());
        assertEquals("completed", res.getStatus());
    }

    @Test
    public void testDefectResponseDeserialization() throws Exception {
        String json = """
        {
            "defect_id": 101,
            "survey_id": 42,
            "class": "pothole",
            "lat": 12.9716,
            "lon": 77.5946,
            "severity": "High",
            "priority": 9.5,
            "estimated_cost": 5000.0,
            "status": "New",
            "crop_path": "crops/101.jpg",
            "recurrence": false
        }
        """;
        DefectResponse res = mapper.readValue(json, DefectResponse.class);
        assertEquals(101, res.getDefectId());
        assertEquals("pothole", res.getDefectClass());
        assertEquals(12.9716, res.getLat(), 0.0001);
        assertEquals(77.5946, res.getLon(), 0.0001);
        assertEquals("High", res.getSeverity());
        assertEquals(9.5, res.getPriority(), 0.001);
        assertEquals(5000.0, res.getEstimatedCost(), 0.001);
        assertEquals("New", res.getStatus());
        assertEquals("crops/101.jpg", res.getCropPath());
        assertFalse(res.isRecurrence());
    }

    @Test
    public void testSegmentResponseDeserialization() throws Exception {
        String json = """
        {
            "segment_id": 201,
            "survey_id": 42,
            "start_m": 0.0,
            "end_m": 50.0,
            "damage_index": 0.035,
            "condition": "Good"
        }
        """;
        SegmentResponse res = mapper.readValue(json, SegmentResponse.class);
        assertEquals(201, res.getSegmentId());
        assertEquals(0.0, res.getStartM(), 0.001);
        assertEquals(50.0, res.getEndM(), 0.001);
        assertEquals(0.035, res.getDamageIndex(), 0.001);
        assertEquals("Good", res.getCondition());
    }
}
