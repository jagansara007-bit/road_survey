package com.roaddamage.ui;

import javafx.application.Application;
import javafx.scene.Scene;
import javafx.scene.control.Tab;
import javafx.scene.control.TabPane;
import javafx.scene.layout.BorderPane;
import javafx.stage.Stage;

public class MainApp extends Application {
    private boolean isDemoMode = false;

    @Override
    public void init() throws Exception {
        var args = getParameters().getRaw();
        if (args.contains("--demo")) {
            isDemoMode = true;
            System.out.println("Running in DEMO mode. Pre-loaded local fixtures active; network bypassed.");
        }
    }

    @Override
    public void start(Stage primaryStage) {
        String title = "Road Damage Authority Dashboard" + (isDemoMode ? " [DEMO MODE]" : "");
        primaryStage.setTitle(title);

        TabPane tabPane = new TabPane();
        tabPane.setTabClosingPolicy(TabPane.TabClosingPolicy.UNAVAILABLE);

        MapView mapView = new MapView(isDemoMode);
        QueueView queueView = new QueueView(isDemoMode);
        VerifyView verifyView = new VerifyView(isDemoMode);
        UploadView uploadView = new UploadView();

        Tab mapTab = new Tab("Map", mapView.getView());
        Tab queueTab = new Tab("Queue", queueView.getView());
        Tab verifyTab = new Tab("Verify", verifyView.getView());
        Tab uploadTab = new Tab("Upload", uploadView.getView());
        
        tabPane.getTabs().addAll(mapTab, queueTab, verifyTab, uploadTab);

        BorderPane root = new BorderPane();
        root.setCenter(tabPane);

        Scene scene = new Scene(root, 1024, 768);
        primaryStage.setScene(scene);
        primaryStage.show();
    }

    public static void main(String[] args) {
        launch(args);
    }
}
