package com.roaddamage.viewmodel;

import com.roaddamage.api.dto.DefectResponse;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.io.PrintWriter;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Map;

public class QueueViewModel {

    private static final Map<String, Integer> SEVERITY_RANK = Map.of(
        "High", 3,
        "Medium", 2,
        "Low", 1
    );

    /**
     * Sort defects by priority desc, severity rank desc, defect_id asc.
     */
    public static List<DefectResponse> buildQueue(List<DefectResponse> defects) {
        List<DefectResponse> queue = new ArrayList<>(defects);
        queue.sort(Comparator
            .comparingDouble((DefectResponse d) -> d.getPriority() != null ? d.getPriority() : 0.0)
            .reversed()
            .thenComparing(Comparator.comparingInt((DefectResponse d) -> SEVERITY_RANK.getOrDefault(d.getSeverity(), 0)).reversed())
            .thenComparingInt(DefectResponse::getDefectId)
        );
        return queue;
    }

    /**
     * Walk the queue in priority order. Include if fits remaining budget, else skip and continue.
     * Identical to Python select_within_budget in app/priority.py.
     */
    public static QueueResult selectWithinBudget(List<DefectResponse> queue, double budgetInr) {
        List<DefectResponse> selected = new ArrayList<>();
        List<DefectResponse> skipped = new ArrayList<>();
        double remaining = budgetInr;

        for (DefectResponse item : queue) {
            double cost = item.getEstimatedCost() != null ? item.getEstimatedCost() : 0.0;
            if (cost <= remaining) {
                selected.add(item);
                remaining -= cost;
            } else {
                skipped.add(item);
            }
        }
        return new QueueResult(selected, skipped, remaining);
    }

    /**
     * Export queue items to CSV.
     */
    public static void exportToCsv(List<DefectResponse> defects, File file) throws IOException {
        try (PrintWriter writer = new PrintWriter(new FileWriter(file))) {
            writer.println("defect_id,class,severity,priority,estimated_cost,status");
            for (DefectResponse d : defects) {
                writer.printf("%d,%s,%s,%.2f,%.2f,%s%n",
                    d.getDefectId(),
                    d.getDefectClass() != null ? d.getDefectClass() : "",
                    d.getSeverity() != null ? d.getSeverity() : "",
                    d.getPriority() != null ? d.getPriority() : 0.0,
                    d.getEstimatedCost() != null ? d.getEstimatedCost() : 0.0,
                    d.getStatus() != null ? d.getStatus() : ""
                );
            }
        }
    }
}
