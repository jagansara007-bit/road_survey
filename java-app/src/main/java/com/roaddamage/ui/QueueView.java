package com.roaddamage.ui;

import com.roaddamage.api.dto.DefectResponse;
import com.roaddamage.demo.DemoDataLoader;
import com.roaddamage.viewmodel.QueueResult;
import com.roaddamage.viewmodel.QueueViewModel;
import javafx.beans.property.SimpleDoubleProperty;
import javafx.beans.property.SimpleIntegerProperty;
import javafx.beans.property.SimpleStringProperty;
import javafx.geometry.Insets;
import javafx.scene.control.*;
import javafx.scene.layout.BorderPane;
import javafx.scene.layout.HBox;
import javafx.scene.layout.VBox;

import java.io.File;
import java.util.ArrayList;
import java.util.List;

public class QueueView {
    private final BorderPane view;
    private final TableView<DefectResponse> table;
    private final Slider budgetSlider;
    private final Label sliderLabel;
    private final List<DefectResponse> allDefects;

    public QueueView() {
        this(false);
    }

    public QueueView(boolean isDemoMode) {
        view = new BorderPane();
        allDefects = new ArrayList<>();

        VBox topControls = new VBox(10);
        topControls.setPadding(new Insets(10));

        HBox sliderBox = new HBox(15);
        sliderLabel = new Label("Budget (INR): ₹50,000");
        sliderLabel.setStyle("-fx-font-weight: bold;");

        budgetSlider = new Slider(0, 1000000, 50000);
        budgetSlider.setShowTickLabels(true);
        budgetSlider.setShowTickMarks(true);
        budgetSlider.setMajorTickUnit(200000);
        budgetSlider.setBlockIncrement(25000);
        budgetSlider.setPrefWidth(400);

        sliderBox.getChildren().addAll(sliderLabel, budgetSlider);

        Button exportBtn = new Button("Export to CSV");
        Label statusMsg = new Label("");
        topControls.getChildren().addAll(sliderBox, exportBtn, statusMsg);

        table = new TableView<>();

        TableColumn<DefectResponse, Integer> idCol = new TableColumn<>("ID");
        idCol.setCellValueFactory(cell -> new SimpleIntegerProperty(cell.getValue().getDefectId()).asObject());
        idCol.setPrefWidth(60);

        TableColumn<DefectResponse, String> classCol = new TableColumn<>("Class");
        classCol.setCellValueFactory(cell -> new SimpleStringProperty(cell.getValue().getDefectClass() != null ? cell.getValue().getDefectClass() : ""));
        classCol.setPrefWidth(120);

        TableColumn<DefectResponse, String> severityCol = new TableColumn<>("Severity");
        severityCol.setCellValueFactory(cell -> new SimpleStringProperty(cell.getValue().getSeverity() != null ? cell.getValue().getSeverity() : ""));
        severityCol.setPrefWidth(90);

        TableColumn<DefectResponse, Double> priorityCol = new TableColumn<>("Priority");
        priorityCol.setCellValueFactory(cell -> new SimpleDoubleProperty(cell.getValue().getPriority() != null ? cell.getValue().getPriority() : 0.0).asObject());
        priorityCol.setPrefWidth(90);

        TableColumn<DefectResponse, Double> costCol = new TableColumn<>("Estimated Cost (₹)");
        costCol.setCellValueFactory(cell -> new SimpleDoubleProperty(cell.getValue().getEstimatedCost() != null ? cell.getValue().getEstimatedCost() : 0.0).asObject());
        costCol.setPrefWidth(140);

        TableColumn<DefectResponse, String> statusCol = new TableColumn<>("Status");
        statusCol.setCellValueFactory(cell -> new SimpleStringProperty(cell.getValue().getStatus() != null ? cell.getValue().getStatus() : ""));
        statusCol.setPrefWidth(90);

        table.getColumns().addAll(idCol, classCol, severityCol, priorityCol, costCol, statusCol);

        if (isDemoMode) {
            List<DefectResponse> loaded = DemoDataLoader.loadDefects();
            allDefects.addAll(QueueViewModel.buildQueue(loaded));
            updateTableForBudget(budgetSlider.getValue());
        }

        budgetSlider.valueProperty().addListener((obs, oldVal, newVal) -> {
            updateTableForBudget(newVal.doubleValue());
        });

        exportBtn.setOnAction(e -> {
            File exportFile = new File("repair_queue_export.csv");
            try {
                QueueViewModel.exportToCsv(table.getItems(), exportFile);
                statusMsg.setText("Exported " + table.getItems().size() + " items to " + exportFile.getName());
                statusMsg.setStyle("-fx-text-fill: green;");
            } catch (Exception ex) {
                statusMsg.setText("Export failed: " + ex.getMessage());
                statusMsg.setStyle("-fx-text-fill: red;");
            }
        });

        view.setTop(topControls);
        view.setCenter(table);
    }

    private void updateTableForBudget(double budget) {
        sliderLabel.setText(String.format("Budget (INR): ₹%,.0f", budget));
        QueueResult result = QueueViewModel.selectWithinBudget(allDefects, budget);
        table.getItems().setAll(result.selected());
    }

    public BorderPane getView() {
        return view;
    }

    public TableView<DefectResponse> getTable() {
        return table;
    }
}
