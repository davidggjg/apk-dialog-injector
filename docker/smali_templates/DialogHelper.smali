docker/smali_templates/DialogHelper.smali
.class public Lmy/app/DialogHelper;
.super Ljava/lang/Object;


.method public static shouldShowDialog(Landroid/content/Context;)Z
    .locals 2
    const-string v0, "dialog_prefs"
    const/4 v1, 0x0
    invoke-virtual {p0, v0, v1}, Landroid/content/Context;->getSharedPreferences(Ljava/lang/String;I)Landroid/content/SharedPreferences;
    move-result-object p0
    const-string v0, "do_not_show"
    invoke-interface {p0, v0, v1}, Landroid/content/SharedPreferences;->getBoolean(Ljava/lang/String;Z)Z
    move-result p0
    if-eqz p0, :cond_0
    const/4 p0, 0x0
    return p0
    :cond_0
    const/4 p0, 0x1
    return p0
.end method


.method public static showDialog(Landroid/content/Context;Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;)V
    .locals 6

    invoke-static {p0}, Lmy/app/DialogHelper;->shouldShowDialog(Landroid/content/Context;)Z
    move-result v0
    if-nez v0, :cond_0
    return-void
    :cond_0

    new-instance v0, Landroid/app/AlertDialog$Builder;
    invoke-direct {v0, p0}, Landroid/app/AlertDialog$Builder;-><init>(Landroid/content/Context;)V

    invoke-virtual {v0, p1}, Landroid/app/AlertDialog$Builder;->setTitle(Ljava/lang/CharSequence;)Landroid/app/AlertDialog$Builder;

    invoke-virtual {v0, p2}, Landroid/app/AlertDialog$Builder;->setMessage(Ljava/lang/CharSequence;)Landroid/app/AlertDialog$Builder;

    new-instance v1, Landroid/widget/CheckBox;
    invoke-direct {v1, p0}, Landroid/widget/CheckBox;-><init>(Landroid/content/Context;)V
    const-string v2, "\u05d0\u05dc \u05ea\u05e6\u05d9\u05d2 \u05e9\u05d5\u05d1"
    invoke-virtual {v1, v2}, Landroid/widget/CheckBox;->setText(Ljava/lang/CharSequence;)V

    invoke-virtual {v0, v1}, Landroid/app/AlertDialog$Builder;->setView(Landroid/view/View;)Landroid/app/AlertDialog$Builder;

    new-instance v2, Lmy/app/DialogHelper$1;
    invoke-direct {v2, v1, p0}, Lmy/app/DialogHelper$1;-><init>(Landroid/widget/CheckBox;Landroid/content/Context;)V
    const-string v3, "\u05d0\u05d9\u05e9\u05d5\u05e8"
    invoke-virtual {v0, v3, v2}, Landroid/app/AlertDialog$Builder;->setPositiveButton(Ljava/lang/CharSequence;Landroid/content/DialogInterface$OnClickListener;)Landroid/app/AlertDialog$Builder;

    const/4 v2, 0x0
    const-string v3, "\u05d1\u05d9\u05d8\u05d5\u05dc"
    invoke-virtual {v0, v3, v2}, Landroid/app/AlertDialog$Builder;->setNegativeButton(Ljava/lang/CharSequence;Landroid/content/DialogInterface$OnClickListener;)Landroid/app/AlertDialog$Builder;

    invoke-virtual {v0}, Landroid/app/AlertDialog$Builder;->create()Landroid/app/AlertDialog;
    move-result-object v0
    invoke-virtual {v0}, Landroid/app/AlertDialog;->show()V

    return-void
.end method
