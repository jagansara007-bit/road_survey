package com.roaddamage.viewmodel;

import com.roaddamage.api.dto.DefectResponse;
import java.util.List;

public record QueueResult(
    List<DefectResponse> selected,
    List<DefectResponse> skipped,
    double remainingBudget
) {}
