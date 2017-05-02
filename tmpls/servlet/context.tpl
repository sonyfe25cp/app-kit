package {{api.ns}};

// Do not edit, auto generated by api-kit, kanzhun.com.
// {{api.ts}}

import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

public class Context {
    public final HttpServletRequest req;
    public final HttpServletResponse resp;
    public final String fname;
    public final String url;
    public Object attachment;
    // return to user as HTTP status code
    public int code = 0;
    public String message; // The error message return to client

    public final long start = System.currentTimeMillis();

    public void setError(int httpCode, String message) {
        this.code = httpCode;
        this.message = message;
    }

    public Context(HttpServletRequest req, HttpServletResponse resp, String fname) {
        this.req = req;
        this.resp = resp;
        this.fname = fname;
        if (req != null) {
            String uri = req.getRequestURI();
            String qs = req.getQueryString();
            if (qs != null && !qs.isEmpty()) {
                uri = uri + "?" + qs;
            }
            this.url = uri;
        } else {
            this.url = "NULL";
        }
    }
}