package com.apkpatcher;

import android.app.Activity;
import android.content.Intent;
import android.content.SharedPreferences;
import android.net.Uri;
import android.os.AsyncTask;
import android.os.Bundle;
import android.view.Menu;
import android.view.MenuItem;
import android.widget.*;
import androidx.appcompat.app.AppCompatActivity;
import org.json.JSONObject;
import java.io.*;
import java.net.*;

public class MainActivity extends AppCompatActivity {

    private static final int PICK_APK = 1;
    private Uri selectedApk;
    private TextView tvApkPath, tvLog;
    private EditText etTitle, etMessage, etButton1, etButton2, etButton3;
    private SharedPreferences prefs;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        prefs = getSharedPreferences("apkpatcher_prefs", MODE_PRIVATE);

        tvApkPath = findViewById(R.id.tvApkPath);
        tvLog     = findViewById(R.id.tvLog);
        etTitle   = findViewById(R.id.etTitle);
        etMessage = findViewById(R.id.etMessage);
        etButton1 = findViewById(R.id.etButton1);
        etButton2 = findViewById(R.id.etButton2);
        etButton3 = findViewById(R.id.etButton3);

        findViewById(R.id.btnSelectApk).setOnClickListener(v -> pickApk());
        findViewById(R.id.btnInject).setOnClickListener(v -> runAction("inject"));
        findViewById(R.id.btnRemove).setOnClickListener(v -> runAction("remove"));
    }

    @Override
    public boolean onCreateOptionsMenu(Menu menu) {
        menu.add(0, 1, 0, "הגדרות")
            .setIcon(android.R.drawable.ic_menu_preferences)
            .setShowAsAction(MenuItem.SHOW_AS_ACTION_ALWAYS);
        return true;
    }

    @Override
    public boolean onOptionsItemSelected(MenuItem item) {
        if (item.getItemId() == 1) {
            startActivity(new Intent(this, SettingsActivity.class));
            return true;
        }
        return super.onOptionsItemSelected(item);
    }

    private String getToken()    { return prefs.getString("github_token", ""); }
    private String getUsername() { return prefs.getString("github_username", ""); }
    private String getRepo()     { return prefs.getString("github_repo", ""); }

    private void pickApk() {
        Intent i = new Intent(Intent.ACTION_GET_CONTENT);
        i.setType("application/vnd.android.package-archive");
        startActivityForResult(i, PICK_APK);
    }

    @Override
    protected void onActivityResult(int req, int res, Intent data) {
        super.onActivityResult(req, res, data);
        if (req == PICK_APK && res == RESULT_OK && data != null) {
            selectedApk = data.getData();
            tvApkPath.setText(selectedApk.getLastPathSegment());
            log("✓ נבחר: " + selectedApk.getLastPathSegment());
        }
    }

    private void runAction(String mode) {
        if (getToken().isEmpty()) {
            toast("הכנס GitHub Token בהגדרות!");
            startActivity(new Intent(this, SettingsActivity.class));
            return;
        }
        if (selectedApk == null) {
            toast("בחר APK קודם!");
            return;
        }
        if (etTitle.getText().toString().isEmpty()) {
            toast("הכנס כותרת!");
            return;
        }
        new PatchTask(mode).execute();
    }

    private void log(String msg) {
        runOnUiThread(() -> tvLog.setText(tvLog.getText() + "\n" + msg));
    }

    private void toast(String msg) {
        runOnUiThread(() -> Toast.makeText(this, msg, Toast.LENGTH_SHORT).show());
    }

    class PatchTask extends AsyncTask<Void, String, Boolean> {
        String mode;
        PatchTask(String mode) { this.mode = mode; }

        @Override
        protected void onPreExecute() {
            tvLog.setText("מתחיל...");
        }

        @Override
        protected Boolean doInBackground(Void... v) {
            try {
                publishProgress("מעדכן הגדרות...");
                updateConfig();

                publishProgress("מעלה APK...");
                uploadApk();

                publishProgress("מפעיל GitHub Action...");
                triggerAction(mode);

                publishProgress("ממתין לסיום...");
                Thread.sleep(30000);

                publishProgress("מוריד תוצאה...");
                downloadResult();

                return true;
            } catch (Exception e) {
                publishProgress("✗ שגיאה: " + e.getMessage());
                return false;
            }
        }

        @Override
        protected void onProgressUpdate(String... values) {
            log(values[0]);
        }

        @Override
        protected void onPostExecute(Boolean success) {
            if (success) {
                log("✓ הושלם! הקובץ נשמר בתיקיית Downloads");
                toast("הושלם בהצלחה!");
            } else {
                log("✗ נכשל");
            }
        }

        private void updateConfig() throws Exception {
            JSONObject cfg = new JSONObject();
            cfg.put("title",   etTitle.getText().toString());
            cfg.put("message", etMessage.getText().toString());
            cfg.put("button1", etButton1.getText().toString());
            cfg.put("button2", etButton2.getText().toString());
            cfg.put("button3", etButton3.getText().toString());

            String content = android.util.Base64.encodeToString(
                cfg.toString().getBytes(), android.util.Base64.NO_WRAP);
            String sha = getFileSha("config.json");

            JSONObject body = new JSONObject();
            body.put("message", "update config");
            body.put("content", content);
            if (sha != null) body.put("sha", sha);

            githubPut("contents/config.json", body.toString());
        }

        private void uploadApk() throws Exception {
            InputStream is = getContentResolver().openInputStream(selectedApk);
            byte[] bytes = toBytes(is);
            String content = android.util.Base64.encodeToString(
                bytes, android.util.Base64.NO_WRAP);
            String name = selectedApk.getLastPathSegment();
            String sha = getFileSha("input/" + name);

            JSONObject body = new JSONObject();
            body.put("message", "upload apk");
            body.put("content", content);
            if (sha != null) body.put("sha", sha);

            githubPut("contents/input/" + name, body.toString());
        }

        private void triggerAction(String mode) throws Exception {
            JSONObject inputs = new JSONObject();
            inputs.put("mode", mode);

            JSONObject body = new JSONObject();
            body.put("ref", "main");
            body.put("inputs", inputs);

            githubPost("actions/workflows/patch.yml/dispatches",
                body.toString());
        }

        private void downloadResult() throws Exception {
            String resp = githubGet("actions/runs?status=completed&per_page=1");
            JSONObject json = new JSONObject(resp);
            String runId = json.getJSONArray("workflow_runs")
                              .getJSONObject(0)
                              .getString("id");

            String artResp = githubGet("actions/runs/" + runId + "/artifacts");
            JSONObject artJson = new JSONObject(artResp);
            String downloadUrl = artJson.getJSONArray("artifacts")
                                       .getJSONObject(0)
                                       .getString("archive_download_url");

            URL url = new URL(downloadUrl);
            HttpURLConnection conn = (HttpURLConnection) url.openConnection();
            conn.setRequestProperty("Authorization", "token " + getToken());
            InputStream is = conn.getInputStream();
            File out = new File(
                android.os.Environment.getExternalStoragePublicDirectory(
                    android.os.Environment.DIRECTORY_DOWNLOADS),
                "patched_signed.apk");
            FileOutputStream fos = new FileOutputStream(out);
            byte[] buf = new byte[4096];
            int n;
            while ((n = is.read(buf)) != -1) fos.write(buf, 0, n);
            fos.close();
        }

        private String getFileSha(String path) {
            try {
                String resp = githubGet("contents/" + path);
                JSONObject j = new JSONObject(resp);
                return j.getString("sha");
            } catch (Exception e) {
                return null;
            }
        }

        private String githubGet(String endpoint) throws Exception {
            URL url = new URL("https://api.github.com/repos/" +
                getUsername() + "/" + getRepo() + "/" + endpoint);
            HttpURLConnection c = (HttpURLConnection) url.openConnection();
            c.setRequestProperty("Authorization", "token " + getToken());
            c.setRequestProperty("Accept", "application/vnd.github.v3+json");
            return new String(toBytes(c.getInputStream()));
        }

        private void githubPut(String endpoint, String body) throws Exception {
            URL url = new URL("https://api.github.com/repos/" +
                getUsername() + "/" + getRepo() + "/" + endpoint);
            HttpURLConnection c = (HttpURLConnection) url.openConnection();
            c.setRequestMethod("PUT");
            c.setRequestProperty("Authorization", "token " + getToken());
            c.setRequestProperty("Content-Type", "application/json");
            c.setDoOutput(true);
            c.getOutputStream().write(body.getBytes());
            toBytes(c.getInputStream());
        }

        private void githubPost(String endpoint, String body) throws Exception {
            URL url = new URL("https://api.github.com/repos/" +
                getUsername() + "/" + getRepo() + "/" + endpoint);
            HttpURLConnection c = (HttpURLConnection) url.openConnection();
            c.setRequestMethod("POST");
            c.setRequestProperty("Authorization", "token " + getToken());
            c.setRequestProperty("Content-Type", "application/json");
            c.setDoOutput(true);
            c.getOutputStream().write(body.getBytes());
            toBytes(c.getInputStream());
        }

        private byte[] toBytes(InputStream is) throws Exception {
            ByteArrayOutputStream bos = new ByteArrayOutputStream();
            byte[] buf = new byte[4096];
            int n;
            while ((n = is.read(buf)) != -1) bos.write(buf, 0, n);
            return bos.toByteArray();
        }
    }
}
