package com.roaddamage.ui;

import javafx.geometry.Insets;
import javafx.geometry.Pos;
import javafx.scene.control.*;
import javafx.scene.layout.GridPane;
import javafx.scene.layout.VBox;

public class UploadView {
    private VBox view;

    public UploadView() {
        view = new VBox(15);
        view.setPadding(new Insets(20));
        view.setAlignment(Pos.TOP_LEFT);

        Label title = new Label("Upload New Survey");
        title.setStyle("-fx-font-size: 16px; -fx-font-weight: bold;");

        GridPane grid = new GridPane();
        grid.setHgap(10);
        grid.setVgap(10);

        grid.add(new Label("Route Name:"), 0, 0);
        TextField routeNameField = new TextField();
        grid.add(routeNameField, 1, 0);

        grid.add(new Label("Survey Date:"), 0, 1);
        DatePicker datePicker = new DatePicker();
        grid.add(datePicker, 1, 1);

        grid.add(new Label("Video File (.mp4):"), 0, 2);
        Button selectVideoBtn = new Button("Browse...");
        grid.add(selectVideoBtn, 1, 2);
        Label videoLabel = new Label("No file selected");
        grid.add(videoLabel, 2, 2);

        grid.add(new Label("GPS Track (.csv/.gpx):"), 0, 3);
        Button selectGpsBtn = new Button("Browse...");
        grid.add(selectGpsBtn, 1, 3);
        Label gpsLabel = new Label("No file selected");
        grid.add(gpsLabel, 2, 3);

        Button submitBtn = new Button("Upload Survey");
        ProgressBar progressBar = new ProgressBar(0);
        progressBar.setPrefWidth(300);
        Label progressLabel = new Label("");

        view.getChildren().addAll(title, grid, submitBtn, progressBar, progressLabel);
    }

    public VBox getView() {
        return view;
    }
}
