package com.apkpatcher;

import android.content.SharedPreferences;
import android.os.Bundle;
import android.widget.Button;
import android.widget.EditText;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;

public class SettingsActivity extends AppCompatActivity {

    private EditText etToken, etUsername, etRepo;
    private SharedPreferences prefs;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_settings);

        prefs = getSharedPreferences("apkpatcher_prefs", MODE_PRIVATE);

        etToken    = findViewById(R.id.etToken);
        etUsername = findViewById(R.id.etUsername);
        etRepo     = findViewById(R.id.etRepo);

        // טען ערכים שמורים
        etToken.setText(prefs.getString("github_token", ""));
        etUsername.setText(prefs.getString("github_username", ""));
        etRepo.setText(prefs.getString("github_repo", ""));

        findViewById(R.id.btnSave).setOnClickListener(v -> saveSettings());
    }

    private void saveSettings() {
        String token    = etToken.getText().toString().trim();
        String username = etUsername.getText().toString().trim();
        String repo     = etRepo.getText().toString().trim();

        if (token.isEmpty() || username.isEmpty() || repo.isEmpty()) {
            Toast.makeText(this, "מלא את כל השדות!", Toast.LENGTH_SHORT).show();
            return;
        }

        prefs.edit()
            .putString("github_token",    token)
            .putString("github_username", username)
            .putString("github_repo",     repo)
            .apply();

        Toast.makeText(this, "נשמר בהצלחה!", Toast.LENGTH_SHORT).show();
        finish();
    }
}
