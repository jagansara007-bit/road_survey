package com.roaddamage.viewmodel;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.roaddamage.api.dto.DefectResponse;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;

import java.io.File;
import java.io.IOException;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

public class QueueViewModelTest {

    private static List<DefectResponse> queue;
    private static JsonNode rootNode;

    @BeforeAll
    public static void setUp() throws IOException {
        ObjectMapper mapper = new ObjectMapper();
        // Path to budget_cases.json
        Path path = Paths.get("..", "data", "fixtures", "budget_cases.json");
        if (!path.toFile().exists()) {
            path = Paths.get("data", "fixtures", "budget_cases.json");
        }
        rootNode = mapper.readTree(path.toFile());
        
        queue = new ArrayList<>();
        for (JsonNode n : rootNode.get("queue")) {
            queue.add(mapper.treeToValue(n, DefectResponse.class));
        }
    }

    @Test
    public void testExactFit() {
        JsonNode caseNode = findCase("exact_fit");
        assertNotNull(caseNode);
        double budget = caseNode.get("budget").asDouble();

        QueueResult result = QueueViewModel.selectWithinBudget(queue, budget);
        assertEquals(1, result.selected().size());
        assertEquals(1, result.selected().get(0).getDefectId());
        assertEquals(0.0, result.remainingBudget(), 0.001);
        assertEquals(3, result.skipped().size());
    }

    @Test
    public void testSkipAndContinue() {
        JsonNode caseNode = findCase("skip_and_continue");
        assertNotNull(caseNode);
        double budget = caseNode.get("budget").asDouble();

        QueueResult result = QueueViewModel.selectWithinBudget(queue, budget);
        assertEquals(2, result.selected().size());
        assertEquals(List.of(1, 3), result.selected().stream().map(DefectResponse::getDefectId).toList());
        assertEquals(0.0, result.remainingBudget(), 0.001);
        assertEquals(List.of(2, 4), result.skipped().stream().map(DefectResponse::getDefectId).toList());
    }

    @Test
    public void testZeroBudget() {
        JsonNode caseNode = findCase("zero_budget");
        assertNotNull(caseNode);
        double budget = caseNode.get("budget").asDouble();

        QueueResult result = QueueViewModel.selectWithinBudget(queue, budget);
        assertTrue(result.selected().isEmpty());
        assertEquals(4, result.skipped().size());
        assertEquals(0.0, result.remainingBudget(), 0.001);
    }

    @Test
    public void testLargeBudget() {
        JsonNode caseNode = findCase("large_budget");
        assertNotNull(caseNode);
        double budget = caseNode.get("budget").asDouble();

        QueueResult result = QueueViewModel.selectWithinBudget(queue, budget);
        assertEquals(4, result.selected().size());
        assertTrue(result.skipped().isEmpty());
        assertEquals(9350.0, result.remainingBudget(), 0.001);
    }

    @Test
    public void testBuildQueueSorting() {
        List<DefectResponse> shuffled = new ArrayList<>(queue);
        // Reverse order
        java.util.Collections.reverse(shuffled);
        
        List<DefectResponse> sorted = QueueViewModel.buildQueue(shuffled);
        assertEquals(1, sorted.get(0).getDefectId());
        assertEquals(2, sorted.get(1).getDefectId());
        assertEquals(3, sorted.get(2).getDefectId());
        assertEquals(4, sorted.get(3).getDefectId());
    }

    private JsonNode findCase(String name) {
        for (JsonNode c : rootNode.get("cases")) {
            if (c.get("name").asText().equals(name)) {
                return c;
            }
        }
        return null;
    }
}
