package app.jay.moonlight;

import android.app.Activity;
import android.app.AlertDialog;
import android.app.DatePickerDialog;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.graphics.LinearGradient;
import android.graphics.RadialGradient;
import android.graphics.Shader;
import android.graphics.RectF;
import android.view.Menu;
import android.view.MenuItem;
import android.widget.PopupMenu;
import android.widget.Toast;
import java.util.Random;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.content.Context;
import android.view.Gravity;
import android.view.View;
import android.widget.Button;
import android.widget.CalendarView;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import com.chaquo.python.Python;
import com.chaquo.python.android.AndroidPlatform;
import org.json.JSONArray;
import org.json.JSONObject;
import java.text.SimpleDateFormat;
import java.util.Calendar;
import java.util.Date;
import java.util.Locale;
import java.util.TimeZone;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/** Offline single-screen client; astronomy stays in the reusable Python module. */
public class MainActivity extends Activity {
    private static final int INK = Color.rgb(7, 13, 27);
    private static final int TEXT = Color.rgb(232, 237, 244);
    private static final int MUTED = Color.rgb(177, 191, 207);
    private final ExecutorService worker = Executors.newSingleThreadExecutor();
    private final Handler main = new Handler(Looper.getMainLooper());
    private TextView phase, illumination, instant, events, status;
    private MoonView moon;
    private CalendarView calendar;
    private long selected;
    private int generation;
    private boolean live = true, updatingCalendar;
    private final Runnable tick = new Runnable() {
        @Override public void run() {
            if (live) { selected = System.currentTimeMillis(); refresh(); }
            main.postDelayed(this, 60000);
        }
    };

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        selected = state == null ? System.currentTimeMillis() : state.getLong("selected");
        live = state == null || state.getBoolean("live");
        ScrollView scroll = new ScrollView(this);
        scroll.setFillViewport(true);
        scroll.setBackground(new NightSky());
        LinearLayout body = new LinearLayout(this);
        body.setOrientation(LinearLayout.VERTICAL);
        body.setPadding(dp(22), dp(24), dp(22), dp(28));
        scroll.addView(body);
        setContentView(scroll);
        TextView brand = text(body, "MOONLIGHT", 14, MUTED);
        brand.setLetterSpacing(.2f);
        Button menu = new Button(this);
        menu.setText("Explore & about  ▾"); menu.setAllCaps(false);
        menu.setOnClickListener(v -> {
            PopupMenu popup = new PopupMenu(this, menu);
            populateMenu(popup.getMenu());
            popup.setOnMenuItemClickListener(this::handleMenu);
            popup.show();
        });
        body.addView(menu);
        text(body, "Your window to the night", 25, TEXT);
        text(body, "Offline • No location needed", 14, MUTED);
        moon = new MoonView(this);
        body.addView(moon, new LinearLayout.LayoutParams(-1, dp(300)));
        phase = text(body, "Calculating…", 28, TEXT);
        phase.setGravity(Gravity.CENTER);
        illumination = text(body, "", 19, TEXT);
        illumination.setGravity(Gravity.CENTER);
        instant = text(body, "", 13, MUTED);
        instant.setGravity(Gravity.CENTER);
        status = text(body, "", 14, MUTED);
        status.setAccessibilityLiveRegion(View.ACCESSIBILITY_LIVE_REGION_POLITE);
        Button now = new Button(this);
        now.setText("Now");
        now.setAllCaps(false);
        now.setOnClickListener(v -> {
            returnToNow();
        });
        body.addView(now, new LinearLayout.LayoutParams(-1, dp(52)));
        text(body, "Explore a date", 21, TEXT);
        text(body, "Calendar selections show 12:00 noon in your device time zone. Now updates each minute.", 14, MUTED);
        calendar = new CalendarView(this);
        calendar.setMinDate(localDate(2001, 0, 2));
        calendar.setMaxDate(localDate(2100, 11, 30));
        calendar.setDate(Math.max(calendar.getMinDate(), Math.min(calendar.getMaxDate(), selected)), false, true);
        body.addView(calendar, new LinearLayout.LayoutParams(-1, dp(340)));
        calendar.setOnDateChangeListener((view, y, m, d) -> {
            if (updatingCalendar) return;
            selected = localDate(y, m, d);
            live = false;
            refresh();
        });
        text(body, "Upcoming new & full moons", 21, TEXT);
        events = text(body, "", 16, TEXT);
        events.setLineSpacing(dp(7), 1f);
        text(body, "Free means free. No ads. No tracking. No account.", 14, MUTED);

    }

    private void returnToNow() {
        live = true; selected = System.currentTimeMillis();
        updatingCalendar = true; calendar.setDate(selected, false, true);
        updatingCalendar = false; refresh();
    }
    private void populateMenu(Menu menu) {
        menu.add(0, 1, 0, "Return to now");
        menu.add(0, 2, 1, "Go to date…");
        menu.add(0, 3, 2, "Copy moon details & events");
        menu.add(0, 4, 3, "About Moonlight");
        menu.add(0, 5, 4, "Privacy — free means free");
        menu.add(0, 6, 5, "Credits & licenses");
        menu.add(0, 7, 6, "Reading the Moon");
        menu.add(0, 8, 7, "Support Kaotick Jay (optional)");
    }
    private void info(String title, String message) {
        TextView content = new TextView(this);
        content.setText(message); content.setTextIsSelectable(true);
        android.text.util.Linkify.addLinks(content, android.text.util.Linkify.WEB_URLS);
        content.setMovementMethod(android.text.method.LinkMovementMethod.getInstance());
        content.setTextSize(16); content.setPadding(dp(24), dp(16), dp(24), dp(16));
        ScrollView scroll = new ScrollView(this); scroll.addView(content);
        new AlertDialog.Builder(this).setTitle(title).setView(scroll).setPositiveButton("Close", null).show();
    }
    private boolean handleMenu(MenuItem item) {
        switch(item.getItemId()) {
            case 1: returnToNow(); break;
            case 2:
                Calendar c = Calendar.getInstance(); c.setTimeInMillis(selected);
                DatePickerDialog picker = new DatePickerDialog(this, (v,y,m,d) -> {
                    selected = localDate(y,m,d); live = false;
                    updatingCalendar = true; calendar.setDate(selected,false,true);
                    updatingCalendar = false; refresh();
                }, c.get(Calendar.YEAR),c.get(Calendar.MONTH),c.get(Calendar.DAY_OF_MONTH));
                picker.getDatePicker().setMinDate(localDate(2001,0,2));
                picker.getDatePicker().setMaxDate(localDate(2100,11,30)); picker.show(); break;
            case 3:
                ((ClipboardManager)getSystemService(CLIPBOARD_SERVICE)).setPrimaryClip(ClipData.newPlainText("Moonlight",
                    phase.getText()+"\n"+illumination.getText()+"\n"+instant.getText()+"\n\n"+events.getText()));
                Toast.makeText(this,"Copied to your clipboard",Toast.LENGTH_SHORT).show(); break;
            case 4: info("About Moonlight", "Moonlight 0.2.1\nCreated by Kaotick Jay.\n\nA free, offline window to the Moon. Current phase, illumination, date exploration and upcoming new and full moons.\n\nFree means free. No ads, subscriptions, accounts or tradeoffs. See Credits & licenses for attribution.\n\nOptional support:\nhttps://github.com/sponsors/kaotickj\nhttps://www.patreon.com/KaotickJay\nhttps://paypal.me/kaotickj\n\nSupport links open your browser; third-party privacy policies apply."); break;
            case 5: info("Free means free", "No advertising. No telemetry. No tracking. No account or email address required. Nothing collected, sold or shared.\n\nAll moon calculations happen on your device. This app requests no Android permissions and makes no network connections itself. Optional support links open external services in your browser only when you choose them. Dates use your device clock and time zone; location is not accessed.\n\nCopy details only writes to your clipboard when you choose it. The app does not read your clipboard."); break;
            case 6:
                String licenses;
                try {
                    java.io.InputStream input = getAssets().open("CREDITS.txt");
                    java.io.ByteArrayOutputStream bytes = new java.io.ByteArrayOutputStream();
                    byte[] buffer = new byte[4096]; int length;
                    while ((length = input.read(buffer)) != -1) bytes.write(buffer,0,length);
                    input.close(); licenses = bytes.toString("UTF-8");
                } catch(Exception e) { licenses = "Credits could not be loaded."; }
                info("Credits & licenses", licenses); break;
            case 7: info("Reading the Moon", "Illumination is the sunlit fraction of the lunar disk. Phase names describe the nearest of eight phase sectors; a Full Moon label does not mean the exact event instant.\n\nThe cratered illustration is decorative: waxing is lit on the right. It does not show your local sky orientation, lunar libration or eclipse darkening.\n\nCalendar dates show local noon. Now refreshes each minute. Event times use your device time zone and the offset at each event.\n\nSupported dates: 2001–2100. Astronomy Engine calculates event times numerically. Selected NASA reference events agree within two minutes; this is not a guarantee across the full range."); break;
            case 8: info("Support Kaotick Jay", "Optional support for Kaotick Jay. Moonlight stays completely free; donations unlock nothing.\n\nGitHub Sponsors: https://github.com/sponsors/kaotickj\nPatreon: https://www.patreon.com/KaotickJay\nPayPal: https://paypal.me/kaotickj\n\nLinks open your browser. Those services have their own privacy policies."); break;
            default: return false;
        }
        return true;
    }
    static class NightSky extends android.graphics.drawable.Drawable {
        private final Paint p = new Paint(Paint.ANTI_ALIAS_FLAG);
        @Override public void draw(Canvas canvas) {
            android.graphics.Rect b = getBounds();
            p.setShader(new LinearGradient(0,0,0,b.height(),new int[]{0xff060b19,0xff15233c,0xff080e1b},null,Shader.TileMode.CLAMP));
            canvas.drawRect(b,p); p.setShader(null);
            Random random = new Random(731);
            for(int i=0;i<180;i++) {
                p.setColor(Color.argb(70+random.nextInt(140),207,222,249));
                canvas.drawCircle(b.left+random.nextFloat()*b.width(),b.top+random.nextFloat()*b.height(),.6f+random.nextFloat()*1.4f,p);
            }
        }
        @Override public void setAlpha(int alpha) {}
        @Override public void setColorFilter(android.graphics.ColorFilter filter) {}
        @Override public int getOpacity() { return android.graphics.PixelFormat.OPAQUE; }
    }

    private long localDate(int y, int m, int d) {
        Calendar c = Calendar.getInstance();
        c.clear();
        c.set(y, m, d, 12, 0, 0);
        return c.getTimeInMillis();
    }
    private String date(long millis) {
        SimpleDateFormat fmt = new SimpleDateFormat("EEE, d MMM yyyy · HH:mm 'UTC'XXX", Locale.getDefault());
        fmt.setTimeZone(TimeZone.getDefault());
        return fmt.format(new Date(millis));
    }
    private TextView text(LinearLayout parent, String label, int size, int color) {
        TextView result = new TextView(this);
        result.setText(label); result.setTextSize(size); result.setTextColor(color);
        result.setPadding(0, dp(5), 0, dp(5));
        parent.addView(result, new LinearLayout.LayoutParams(-1, -2));
        return result;
    }
    private int dp(int value) { return Math.round(value * getResources().getDisplayMetrics().density); }

    private void refresh() {
        final int request = ++generation;
        final long time = selected;
        instant.setText((live ? "Now · " : "Selected date · ") + date(time) + "\n" + TimeZone.getDefault().getID());
        status.setText("Calculating…");
        phase.setText("Calculating…");
        illumination.setText("");
        events.setText("");
        worker.execute(() -> {
            try {
                synchronized (Python.class) {
                    if (!Python.isStarted()) Python.start(new AndroidPlatform(getApplicationContext()));
                }
                JSONObject result = new JSONObject(Python.getInstance().getModule("moon")
                    .callAttr("moon_data", time).toString());
                main.post(() -> {
                    if (request != generation || isDestroyed()) return;
                    try {
                        String name = result.getString("phase_name");
                        double lit = result.getDouble("illumination");
                        phase.setText(name);
                        illumination.setText(String.format(Locale.getDefault(), "%.1f%% illuminated", lit * 100));
                        moon.update(lit, result.getDouble("phase_degrees") < 180);
                        moon.setContentDescription(name + ", " + illumination.getText());
                        JSONArray list = result.getJSONArray("events");
                        StringBuilder details = new StringBuilder();
                        for (int i = 0; i < list.length(); ++i) {
                            JSONObject event = list.getJSONObject(i);
                            if (i > 0) details.append("\n\n");
                            details.append(event.getString("name")).append("\n").append(date(event.getLong("epoch_ms")));
                        }
                        events.setText(list.length() == 0 ? "No further events in the supported range." : details.toString());
                        status.setText(list.length() < 4 ? "Event list ends at the supported year 2100." : "");
                    } catch (Exception e) { showError(); }
                });
            } catch (Exception e) {
                main.post(() -> { if (request == generation && !isDestroyed()) showError(); });
            }
        });
    }
    private void showError() {
        phase.setText("Unable to calculate");
        illumination.setText(""); events.setText("");
        moon.update(0, true);
        moon.setContentDescription("Moon illustration unavailable");
        status.setText("Choose a date between 2001 and 2100, then try again.");
    }
    @Override protected void onResume() { super.onResume(); main.post(tick); if (!live) refresh(); }
    @Override protected void onPause() { main.removeCallbacks(tick); super.onPause(); }
    @Override protected void onSaveInstanceState(Bundle out) {
        out.putLong("selected", selected); out.putBoolean("live", live); super.onSaveInstanceState(out);
    }
    @Override protected void onDestroy() {
        ++generation; main.removeCallbacks(tick); worker.shutdownNow(); super.onDestroy();
    }
    static class MoonView extends View {
        private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
        private double fraction;
        private boolean waxing;
        MoonView(Context context) { super(context); }
        void update(double value, boolean isWaxing) { fraction = value; waxing = isWaxing; invalidate(); }
        @Override protected void onDraw(Canvas canvas) {
            float cx = getWidth() / 2f, cy = getHeight() / 2f;
            float radius = Math.min(getWidth(), getHeight()) * .39f;
            paint.setShader(new RadialGradient(cx,cy,radius*1.35f,new int[]{0x30cadbff,0x00cadbff},null,Shader.TileMode.CLAMP));
            canvas.drawCircle(cx,cy,radius*1.35f,paint); paint.setShader(null);
            paint.setColor(Color.rgb(30, 39, 55)); canvas.drawCircle(cx,cy,radius,paint);
            int saved = canvas.save();
            canvas.clipPath(disk(cx,cy,radius));
            paint.setShader(new RadialGradient(cx-radius*.3f,cy-radius*.4f,radius*1.8f,new int[]{0xfff2eedc,0xffa6acb3},null,Shader.TileMode.CLAMP));
            canvas.drawCircle(cx,cy,radius,paint); paint.setShader(null);
            Random random = new Random(41);
            for(int i=0;i<90;i++) {
                float x=cx+(random.nextFloat()*2-1)*radius, y=cy+(random.nextFloat()*2-1)*radius;
                float r=radius*(.014f+random.nextFloat()*.065f);
                paint.setColor(0x23515b69); canvas.drawCircle(x,y,r,paint);
                paint.setColor(0x20ffffff); paint.setStyle(Paint.Style.STROKE); paint.setStrokeWidth(1);
                canvas.drawCircle(x,y,r,paint); paint.setStyle(Paint.Style.FILL);
            }
            paint.setColor(0xed10192a); paint.setStrokeWidth(1.5f);
            for (float y = -radius; y <= radius; y += 1) {
                float edge = (float)Math.sqrt(Math.max(0, radius * radius - y * y));
                float terminator = (float)((1 - 2 * fraction) * edge);
                if (waxing) canvas.drawLine(cx-edge,cy+y,cx+terminator,cy+y,paint);
                else canvas.drawLine(cx-terminator,cy+y,cx+edge,cy+y,paint);
            }
            canvas.restoreToCount(saved);
        }
        private android.graphics.Path disk(float x,float y,float r) {
            android.graphics.Path path = new android.graphics.Path();
            path.addCircle(x,y,r,android.graphics.Path.Direction.CW); return path;
        }
    }
}
