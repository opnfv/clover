# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: proxy.proto

import sys
_b=sys.version_info[0]<3 and (lambda x:x) or (lambda x:x.encode('latin1'))
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
from google.protobuf import descriptor_pb2
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='proxy.proto',
  package='proxy',
  syntax='proto3',
  serialized_pb=_b('\n\x0bproxy.proto\x12\x05proxy\"3\n\x0c\x41lertMessage\x12\x10\n\x08\x65vent_id\x18\x01 \x01(\t\x12\x11\n\tredis_key\x18\x02 \x01(\t\"1\n\tAddConfig\x12\x10\n\x08protocol\x18\x01 \x01(\t\x12\x12\n\nproxy_port\x18\x02 \x01(\t\"\x1d\n\nProxyReply\x12\x0f\n\x07message\x18\x01 \x01(\t2~\n\nController\x12\x35\n\x0cModifyConfig\x12\x10.proxy.AddConfig\x1a\x11.proxy.ProxyReply\"\x00\x12\x39\n\rProcessAlerts\x12\x13.proxy.AlertMessage\x1a\x11.proxy.ProxyReply\"\x00\x62\x06proto3')
)




_ALERTMESSAGE = _descriptor.Descriptor(
  name='AlertMessage',
  full_name='proxy.AlertMessage',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='event_id', full_name='proxy.AlertMessage.event_id', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='redis_key', full_name='proxy.AlertMessage.redis_key', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=22,
  serialized_end=73,
)


_ADDCONFIG = _descriptor.Descriptor(
  name='AddConfig',
  full_name='proxy.AddConfig',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='protocol', full_name='proxy.AddConfig.protocol', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='proxy_port', full_name='proxy.AddConfig.proxy_port', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=75,
  serialized_end=124,
)


_PROXYREPLY = _descriptor.Descriptor(
  name='ProxyReply',
  full_name='proxy.ProxyReply',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='message', full_name='proxy.ProxyReply.message', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=126,
  serialized_end=155,
)

DESCRIPTOR.message_types_by_name['AlertMessage'] = _ALERTMESSAGE
DESCRIPTOR.message_types_by_name['AddConfig'] = _ADDCONFIG
DESCRIPTOR.message_types_by_name['ProxyReply'] = _PROXYREPLY
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

AlertMessage = _reflection.GeneratedProtocolMessageType('AlertMessage', (_message.Message,), dict(
  DESCRIPTOR = _ALERTMESSAGE,
  __module__ = 'proxy_pb2'
  # @@protoc_insertion_point(class_scope:proxy.AlertMessage)
  ))
_sym_db.RegisterMessage(AlertMessage)

AddConfig = _reflection.GeneratedProtocolMessageType('AddConfig', (_message.Message,), dict(
  DESCRIPTOR = _ADDCONFIG,
  __module__ = 'proxy_pb2'
  # @@protoc_insertion_point(class_scope:proxy.AddConfig)
  ))
_sym_db.RegisterMessage(AddConfig)

ProxyReply = _reflection.GeneratedProtocolMessageType('ProxyReply', (_message.Message,), dict(
  DESCRIPTOR = _PROXYREPLY,
  __module__ = 'proxy_pb2'
  # @@protoc_insertion_point(class_scope:proxy.ProxyReply)
  ))
_sym_db.RegisterMessage(ProxyReply)



_CONTROLLER = _descriptor.ServiceDescriptor(
  name='Controller',
  full_name='proxy.Controller',
  file=DESCRIPTOR,
  index=0,
  options=None,
  serialized_start=157,
  serialized_end=283,
  methods=[
  _descriptor.MethodDescriptor(
    name='ModifyConfig',
    full_name='proxy.Controller.ModifyConfig',
    index=0,
    containing_service=None,
    input_type=_ADDCONFIG,
    output_type=_PROXYREPLY,
    options=None,
  ),
  _descriptor.MethodDescriptor(
    name='ProcessAlerts',
    full_name='proxy.Controller.ProcessAlerts',
    index=1,
    containing_service=None,
    input_type=_ALERTMESSAGE,
    output_type=_PROXYREPLY,
    options=None,
  ),
])
_sym_db.RegisterServiceDescriptor(_CONTROLLER)

DESCRIPTOR.services_by_name['Controller'] = _CONTROLLER

# @@protoc_insertion_point(module_scope)
