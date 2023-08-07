Window为主窗口

```mermaid
graph TD
    a[Window];
    b[LoginLayout];
    c[ChatLayout];
    d[QtHackchatPort];
    a --signals_window--> c;
    b --"signals_window\nsignals_loginlayout\nnick\npassword\nchannel"--> d;
    a --signals_window--> b;