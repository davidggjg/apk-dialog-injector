.class Lmy/app/DialogHelper$1;
.super Ljava/lang/Object;
.implements Landroid/content/DialogInterface$OnClickListener;

# fields
.field final synthetic val$checkBox:Landroid/widget/CheckBox;
.field final synthetic val$context:Landroid/content/Context;


# direct methods
.method constructor <init>(Landroid/widget/CheckBox;Landroid/content/Context;)V
    .locals 0
    iput-object p1, p0, Lmy/app/DialogHelper$1;->val$checkBox:Landroid/widget/CheckBox;
    iput-object p2, p0, Lmy/app/DialogHelper$1;->val$context:Landroid/content/Context;
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V
    return-void
.end method


# virtual methods
.method public onClick(Landroid/content/DialogInterface;I)V
    .locals 1

    # בדיקה אם ה‑CheckBox מסומן
    iget-object p1, p0, Lmy/app/DialogHelper$1;->val$checkBox:Landroid/widget/CheckBox;
    invoke-virtual {p1}, Landroid/widget/CheckBox;->isChecked()Z
    move-result p1
    if-eqz p1, :cond_0
        # שמירה ב‑SharedPreferences
        iget-object p1, p0, Lmy/app/DialogHelper$1;->val$context:Landroid/content/Context;
        const-string p2, "dialog_prefs"
        const/4 v0, 0x0
        invoke-virtual {p1, p2, v0}, Landroid/content/Context;->getSharedPreferences(Ljava/lang/String;I)Landroid/content/SharedPreferences;
        move-result-object p1
        invoke-interface {p1}, Landroid/content/SharedPreferences;->edit()Landroid/content/SharedPreferences$Editor;
        move-result-object p1
        const-string p2, "do_not_show"
        const/4 v0, 0x1
        invoke-interface {p1, p2, v0}, Landroid/content/SharedPreferences$Editor;->putBoolean(Ljava/lang/String;Z)Landroid/content/SharedPreferences$Editor;
        invoke-interface {p1}, Landroid/content/SharedPreferences$Editor;->apply()V
    :cond_0
    return-void
.end method
