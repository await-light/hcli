Window为主窗口

```mermaid
graph TD
    a[Window];
    b[LoginLayout];
    c[ChatLayout];
    d[QtHackchatPort];
    e[QtDataHandler];
    f[SendTextEdit];
    a --signals_window\nws connection\nfirst_msg--> c;
    b --"signals_window\nsignals_loginlayout\nnick\npassword\nchannel"--> d;
    a --signals_window--> b;
    d --ws connection\nfirst_msg--> a;
    c --signals_window\nsignals_chatlayout\nws connection--> e;
    c --signals_window\nsignals_chatlayout--> f;
