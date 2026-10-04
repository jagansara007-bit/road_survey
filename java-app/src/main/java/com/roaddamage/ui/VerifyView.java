package com.roaddamage.ui;

import javafx.geometry.Insets;
import javafx.geometry.Pos;
import javafx.scene.control.Button;
import javafx.scene.control.Label;
import javafx.scene.image.ImageView;
import javafx.scene.layout.BorderPane;
import javafx.scene.layout.HBox;
import javafx.scene.layout.VBox;

public class VerifyView {
    private final BorderPane view;
    private final ImageView oldCropView;
    private final ImageView newCropView;
    private final Label statusLabel;

    public VerifyView() {
        this(false);
    }

    public VerifyView(boolean isDemoMode) {
        view = new BorderPane();
        view.setPadding(new Insets(15));
        
        Label title = new Label("Verify Contractor Repair Status");
        title.setStyle("-fx-font-size: 16px; -fx-font-weight: bold;");
        view.setTop(title);
        BorderPane.setAlignment(title, Pos.CENTER);
        
        HBox imageBox = new HBox(20);
        imageBox.setAlignment(Pos.CENTER);
        
        VBox oldBox = new VBox(10);
        oldBox.setAlignment(Pos.CENTER);
        oldBox.getChildren().add(new Label("Previous Survey (Baseline)"));
        oldCropView = new ImageView();
        oldCropView.setFitWidth(300);
        oldCropView.setFitHeight(300);
        oldCropView.setPreserveRatio(true);
        oldCropView.setStyle("-fx-background-color: #dee2e6;");
        oldBox.getChildren().add(oldCropView);
        
        VBox newBox = new VBox(10);
        newBox.setAlignment(Pos.CENTER);
        newBox.getChildren().add(new Label("Current Survey (Re-survey)"));
        newCropView = new ImageView();
        newCropView.setFitWidth(300);
        newCropView.setFitHeight(300);
        newCropView.setPreserveRatio(true);
        newCropView.setStyle("-fx-background-color: #dee2e6;");
        newBox.getChildren().add(newCropView);
        
        imageBox.getChildren().addAll(oldBox, newBox);
        view.setCenter(imageBox);
        
        VBox bottomControls = new VBox(10);
        bottomControls.setAlignment(Pos.CENTER);
        
        statusLabel = new Label(isDemoMode ? "Current Status: Pothole #1 (MG Road, Bengaluru) — Verification Pending" : "Current Status: Unknown");
        statusLabel.setStyle("-fx-font-weight: bold; -fx-font-size: 14px;");
        
        HBox actionBox = new HBox(15);
        actionBox.setAlignment(Pos.CENTER);
        Button btnRepaired = new Button("Mark as Repaired");
        btnRepaired.setStyle("-fx-background-color: #2b8a3e; -fx-text-fill: white; -fx-font-weight: bold;");
        btnRepaired.setOnAction(e -> statusLabel.setText("Current Status: Repaired (Verified Closed)"));

        Button btnFailed = new Button("Mark as Failed");
        btnFailed.setStyle("-fx-background-color: #c92a2a; -fx-text-fill: white; -fx-font-weight: bold;");
        btnFailed.setOnAction(e -> statusLabel.setText("Current Status: Failed (Defect Recurred / Inadequate Repair)"));

        Button btnOpen = new Button("Keep Open");
        btnOpen.setOnAction(e -> statusLabel.setText("Current Status: Open (Unrepaired)"));

        actionBox.getChildren().addAll(btnRepaired, btnFailed, btnOpen);
        
        bottomControls.getChildren().addAll(statusLabel, actionBox);
        view.setBottom(bottomControls);
    }

    public BorderPane getView() {
        return view;
    }
}
