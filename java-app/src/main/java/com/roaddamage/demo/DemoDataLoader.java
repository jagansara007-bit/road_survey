package com.roaddamage.demo;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.roaddamage.api.dto.DefectResponse;

import java.io.InputStream;
import java.util.List;
import java.util.Collections;

public class DemoDataLoader {
    public static List<DefectResponse> loadDefects() {
        try {
            ObjectMapper mapper = new ObjectMapper();
            InputStream is = DemoDataLoader.class.getResourceAsStream("/demo/fixtures.json");
            if (is == null) {
                System.err.println("Could not find fixtures.json");
                return Collections.emptyList();
            }
            return mapper.readValue(is, new TypeReference<List<DefectResponse>>() {});
        } catch (Exception e) {
            e.printStackTrace();
            return Collections.emptyList();
        }
    }
}
