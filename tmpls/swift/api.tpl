import Foundation

class Api {
    var queue:NSOperationQueue = NSOperationQueue()
    var host:NSString = ""

    init(host:NSString) {
        self.host = host
    }

{% for func in api.funcs %}
    // {{func.method}} {{func.uri}}
    func {{func.name}}({% for arg in func.params %}{{arg.name}}:{{arg.type('swift')}}, {% end %} completionHandler handler: (NSURLResponse!, {{func.ret.type('swift')}}!, NSError!) -> Void) {
    {% set url, args, qs = func.concat_url('swift') %}
    {% if func.method == 'POST' %}
        let url = "\(host){{url}}"
        var request = NSMutableURLRequest(URL: NSURL(string: url)!)
        request.HTTPMethod = "POST"
        // TODO url escape
        request.HTTPBody = "{{qs}}".dataUsingEncoding(NSUTF8StringEncoding, allowLossyConversion: true)
    {% else %}
        let url = "\(host){{url}}{{qs}}"
        let request = NSURLRequest(URL: NSURL(string: url)!)
    {% end %}
        NSURLConnection.sendAsynchronousRequest(request, queue: self.queue) { (resp:NSURLResponse!, data: NSData!, error: NSError!) -> Void in
            if error != nil {
                handler(resp, nil, error)
                return
            }
        {% if not func.ret.is_primitive %}
            var e:NSError?
            var obj:AnyObject? = NSJSONSerialization.JSONObjectWithData(data, options: NSJSONReadingOptions.MutableContainers, error: &e)
            if e != nil {
                handler(resp, nil, e)
                return
            }
        {% end %}
        {% if func.ret.list %}
            var ret:{{func.ret.type('swift')}} = []
            if let arr = obj as? NSArray {
                for a in arr {
            {% if func.ret.list_item.is_primitive %}
                    if let v = a as? {{func.ret.list_item.type("swift")}} {
                         ret.append(v)
                    }
            {% else %}
                    if let v = a as? NSDictionary {
                        ret.append({{func.ret.list_item.t}}(d: v))
                    }
            {% end %}
                }
            }
            handler(resp, ret, nil)
        {% elif 'string' in func.ret.t %}
            handler(resp, NSString(data: data, encoding: NSUTF8StringEncoding), nil)
        {% else %}
            var ret:{{func.ret.type('swift')}} = {{func.ret.type('swift')}}()
            if let d = obj as? NSDictionary {
                ret = {{func.ret.type('swift')}}(d: d)
            }
            handler(resp, ret, nil)
        {% end%}
        }
    }
{% end %}
}