#import <Foundation/Foundation.h>
#import "{{api.ns}}Beans.h"

// Do not edit, auto generated by api-kit, kanzhun.com.
// {{api.ts}}

typedef NSMutableURLRequest* (^{{api.ns}}RequestHooker)(NSMutableURLRequest* req, NSString* name);

@interface {{api.ns}}Api : NSObject

@property (strong, nonatomic) NSString *server;
@property (nonatomic, copy) {{api.ns}}RequestHooker hooker;
@property (strong, nonatomic) NSOperationQueue *queue;

- (id) init: (NSString *) server hooker:({{api.ns}}RequestHooker)hooker;

- (NSString*) encode: (NSString *) v;

{% for func in api.funcs %}
// {{func.ret.t}} {{func.method}} {{func.uri}}
- (void) {{func.name}}: {% for idx, arg in enumerate(func.params) %} {% if idx > 0 %}{{arg.name}}:{% end %}({{arg.type('objc')}}){{arg.name}} {% end %} completionHandler:(void (^)(NSURLResponse* response, {{func.ret.type('objc')}}data, NSError* connectionError)) handler;

{% end %}

{% for b in api.batches %}
// POST {{b.uri}}
- (void) {{b.name}}: {% for idx, (f, arg, resp) in enumerate(b.params) %} {% if idx > 0 %}{{arg.name}}:{% end %}({{arg.type('objc')}}) {{arg.name}} {% end %} completionHandler:(void (^)(NSURLResponse* response, {{api.ns}}{{b.name}}Resp* data, NSError* connectionError)) handler;
{% end %}

@end