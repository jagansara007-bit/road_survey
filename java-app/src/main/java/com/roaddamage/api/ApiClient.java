package com.roaddamage.api;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.roaddamage.api.dto.DefectResponse;
import com.roaddamage.api.dto.SegmentResponse;
import com.roaddamage.api.dto.SurveyResponse;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.util.List;

public class ApiClient {
    private final String baseUrl;
    private final String apiKey;
    private final HttpClient httpClient;
    private final ObjectMapper objectMapper;

    public ApiClient(String baseUrl, String apiKey) {
        this.baseUrl = baseUrl;
        this.apiKey = apiKey;
        this.httpClient = HttpClient.newHttpClient();
        this.objectMapper = new ObjectMapper();
    }

    private HttpRequest.Builder requestBuilder(String path) {
        return HttpRequest.newBuilder()
                .uri(URI.create(baseUrl + path))
                .header("X-API-Key", apiKey)
                .header("Accept", "application/json");
    }

    public List<SurveyResponse> getSurveys() throws Exception {
        HttpRequest request = requestBuilder("/surveys").GET().build();
        HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
        if (response.statusCode() != 200) {
            throw new RuntimeException("Failed to get surveys: " + response.body());
        }
        return objectMapper.readValue(response.body(),
                objectMapper.getTypeFactory().constructCollectionType(List.class, SurveyResponse.class));
    }

    public List<DefectResponse> getDefects(int surveyId) throws Exception {
        HttpRequest request = requestBuilder("/surveys/" + surveyId + "/defects").GET().build();
        HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
        if (response.statusCode() != 200) {
            throw new RuntimeException("Failed to get defects: " + response.body());
        }
        return objectMapper.readValue(response.body(),
                objectMapper.getTypeFactory().constructCollectionType(List.class, DefectResponse.class));
    }

    public List<SegmentResponse> getSegments(int surveyId) throws Exception {
        HttpRequest request = requestBuilder("/surveys/" + surveyId + "/segments").GET().build();
        HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
        if (response.statusCode() != 200) {
            throw new RuntimeException("Failed to get segments: " + response.body());
        }
        return objectMapper.readValue(response.body(),
                objectMapper.getTypeFactory().constructCollectionType(List.class, SegmentResponse.class));
    }
}
