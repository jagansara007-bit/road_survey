package com.roaddamage.ui;

import com.roaddamage.api.dto.DefectResponse;
import com.roaddamage.demo.DemoDataLoader;
import javafx.concurrent.Worker;
import javafx.scene.layout.BorderPane;
import javafx.scene.web.WebEngine;
import javafx.scene.web.WebView;
import netscape.javascript.JSObject;

import java.net.URL;
import java.util.List;

public class MapView {
    private final BorderPane view;
    private final WebView webView;
    private final WebEngine webEngine;
    private final boolean isDemoMode;

    public MapView() {
        this(false);
    }

    public MapView(boolean isDemoMode) {
        this.isDemoMode = isDemoMode;
        this.view = new BorderPane();
        this.webView = new WebView();
        this.webEngine = webView.getEngine();

        URL mapUrl = getClass().getResource("/map.html");
        if (mapUrl != null) {
            webEngine.load(mapUrl.toExternalForm());
        } else {
            System.err.println("Could not find map.html in resources.");
        }

        webEngine.getLoadWorker().stateProperty().addListener((obs, oldState, newState) -> {
            if (newState == Worker.State.SUCCEEDED) {
                JSObject window = (JSObject) webEngine.executeScript("window");
                window.setMember("javaApp", new JavaBridge());

                if (this.isDemoMode) {
                    loadDemoMarkers();
                }
            }
        });

        view.setCenter(webView);
    }

    private void loadDemoMarkers() {
        List<DefectResponse> defects = DemoDataLoader.loadDefects();
        for (DefectResponse d : defects) {
            addDefectToMap(d.getDefectId(), d.getLat(), d.getLon(), d.getSeverity());
        }
        if (!defects.isEmpty()) {
            DefectResponse first = defects.get(0);
            setView(first.getLat(), first.getLon(), 16);
        }
    }

    public BorderPane getView() {
        return view;
    }

    public void addDefectToMap(int id, double lat, double lon, String severity) {
        if (webEngine.getLoadWorker().getState() == Worker.State.SUCCEEDED) {
            webEngine.executeScript(String.format("addDefect(%d, %f, %f, '%s')", id, lat, lon, severity));
        }
    }

    public void setView(double lat, double lon, int zoom) {
        if (webEngine.getLoadWorker().getState() == Worker.State.SUCCEEDED) {
            webEngine.executeScript(String.format("setView(%f, %f, %d)", lat, lon, zoom));
        }
    }

    public class JavaBridge {
        public void selectDefect(int id) {
            System.out.println("Defect selected from map: " + id);
        }
    }
}
