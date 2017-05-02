#import "{{api.ns}}Api.h"

// Do not edit, auto generated by api-kit, kanzhun.com.
// {{api.ts}}

@implementation {{api.ns}}Api

- (id) init: (NSString *) server hooker:({{api.ns}}RequestHooker)hooker {
    if (self=[super init]) {
        self.server = server;
        self.queue = [[NSOperationQueue alloc] init];
        self.hooker = hooker;
    }
    return self;
}

- (NSString*) encode: (NSString *) v {
    return (NSString *)CFBridgingRelease(CFURLCreateStringByAddingPercentEscapes(NULL,
                                                               (CFStringRef)v,
                                                               NULL,
                                                               (CFStringRef)@"!*'\"();:@&=+$,/?%#[]% ",
                                                               CFStringConvertNSStringEncodingToEncoding(NSUTF8StringEncoding)));
}

{% set primitives = {'i32': 'intValue', 'i64': 'longValue', 'float32': 'floatValue', 'float64': 'doubleValue', 'bool': 'boolValue'} %}

{% for b in api.batches %}
// POST {{b.uri}}
- (void) {{b.name}}: {% for idx, (f, arg, resp) in enumerate(b.params) %} {% if idx > 0 %}{{arg.name}}:{% end %}({{arg.type('objc')}}) {{arg.name}} {% end %} completionHandler:(void (^)(NSURLResponse* response, {{api.ns}}{{b.name}}Resp* data, NSError* connectionError)) handler {
    NSString *__url = [NSString stringWithFormat: @"%@{{b.uri}}", self.server];
    NSMutableURLRequest *__req = [NSMutableURLRequest requestWithURL:[NSURL URLWithString:__url]];
    if (self.hooker) {
        __req = self.hooker(__req, @"{{b.name}}");
    }

    id __body = [[[{{api.ns}}{{b.name}}Req alloc] init:{% for idx, (f, arg, resp) in enumerate(b.params) %} {% if idx > 0 %}{{arg.name}}:{% end %}{{arg.name}} {% end %}] toJSON];
    __req.HTTPMethod = @"POST";
    __req.HTTPBody = [NSJSONSerialization dataWithJSONObject:__body options:kNilOptions error:nil];
    [NSURLConnection sendAsynchronousRequest:__req queue:self.queue completionHandler:^(NSURLResponse *response, NSData *data, NSError *connectionError) {
        if (connectionError != nil || data == nil) {
            handler(response, nil, connectionError);
            return;
        }
        NSError *error = nil;
        id dict = [NSJSONSerialization JSONObjectWithData:data options:kNilOptions error:&error];
        if (error != nil) {
            handler(response, nil, error);
            return;
        }
        handler(response, [[{{api.ns}}{{b.name}}Resp alloc] initWithDict:dict], nil);
    }];
}
{% end %}


{% for func in api.funcs %}
// {{func.ret.t}} {{func.method}} {{func.uri}}
- (void) {{func.name}}: {% for idx, arg in enumerate(func.params) %}{% if idx > 0 %}{{arg.name}}:{% end %}({{arg.type('objc')}}){{arg.name}} {% end %}completionHandler:(void (^)(NSURLResponse* response, {{func.ret.type('objc')}}data, NSError* connectionError)) handler {
    {% set uri, args, (body, bodyparams) = func.concat_url('objc') %}
    NSString *__url = [NSString stringWithFormat: @"%@{{uri}}", self.server {% for a in args %}, {{a}} {% end %}];
    NSMutableURLRequest *__req = [NSMutableURLRequest requestWithURL:[NSURL URLWithString:__url]];
{% if func.method == 'POST' %}
    __req.HTTPMethod = @"POST";
    NSString *__body = [NSString stringWithFormat: @"{{body}}" {% for a in bodyparams %}, {{a}} {% end %}];
    __req.HTTPBody = [__body dataUsingEncoding:NSUTF8StringEncoding];
{% end %}
    if (self.hooker) {
        __req = self.hooker(__req, @"{{func.name}}");
    }

    [NSURLConnection sendAsynchronousRequest:__req queue:self.queue completionHandler:^(NSURLResponse *response, NSData *data, NSError *connectionError) {
        if (connectionError != nil || data == nil) {
            handler(response, nil, connectionError);
            return;
        }
    {% if func.ret.t == 'string' %}
        handler(response, [[NSString alloc] initWithData:data encoding:NSUTF8StringEncoding], nil);
    {% else %}
        NSError *error = nil;
        id dict = [NSJSONSerialization JSONObjectWithData:data options:kNilOptions error:&error];
        if (error != nil) {
            handler(response, nil, error);
            return;
        }
{% if func.ret.list %}
        NSMutableArray *__arr = [[NSMutableArray alloc] init];
        if ([dict isKindOfClass:[NSArray class]]) {
            for (int i=0; i<[dict count]; i++) {
        {% if func.ret.list_item.t in primitives %}
                [__arr addObject:[[dict objectAtIndex:i] {{primitives[func.ret.list_item.t]}}];
        {% elif func.ret.list_item.t == 'string' %}
                [__arr addObject:[dict objectAtIndex:i]];
        {% else %}
                [__arr addObject:[[{{func.ret.list_item.type('objc', 1)}} alloc] initWithDict:[dict objectAtIndex:i]]];
        {% end %}
            }
        }
        handler(response, __arr, nil);
{% else %}
        handler(response, [[{{func.ret.type('objc', 1)}} alloc] initWithDict:dict], nil);
{% end %}
    {% end %}
    }];
}
{% end %}

@end