# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
import grpc

import nginx_pb2 as nginx__pb2


class ControllerStub(object):
  """The controller service definition.
  """

  def __init__(self, channel):
    """Constructor.

    Args:
      channel: A grpc.Channel.
    """
    self.ModifyProxy = channel.unary_unary(
        '/nginx.Controller/ModifyProxy',
        request_serializer=nginx__pb2.ConfigProxy.SerializeToString,
        response_deserializer=nginx__pb2.NginxReply.FromString,
        )
    self.ModifyServer = channel.unary_unary(
        '/nginx.Controller/ModifyServer',
        request_serializer=nginx__pb2.ConfigServer.SerializeToString,
        response_deserializer=nginx__pb2.NginxReply.FromString,
        )
    self.ModifyLB = channel.unary_unary(
        '/nginx.Controller/ModifyLB',
        request_serializer=nginx__pb2.ConfigLB.SerializeToString,
        response_deserializer=nginx__pb2.NginxReply.FromString,
        )
    self.ProcessAlerts = channel.unary_unary(
        '/nginx.Controller/ProcessAlerts',
        request_serializer=nginx__pb2.AlertMessage.SerializeToString,
        response_deserializer=nginx__pb2.NginxReply.FromString,
        )


class ControllerServicer(object):
  """The controller service definition.
  """

  def ModifyProxy(self, request, context):
    # missing associated documentation comment in .proto file
    pass
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')

  def ModifyServer(self, request, context):
    # missing associated documentation comment in .proto file
    pass
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')

  def ModifyLB(self, request, context):
    # missing associated documentation comment in .proto file
    pass
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')

  def ProcessAlerts(self, request, context):
    # missing associated documentation comment in .proto file
    pass
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')


def add_ControllerServicer_to_server(servicer, server):
  rpc_method_handlers = {
      'ModifyProxy': grpc.unary_unary_rpc_method_handler(
          servicer.ModifyProxy,
          request_deserializer=nginx__pb2.ConfigProxy.FromString,
          response_serializer=nginx__pb2.NginxReply.SerializeToString,
      ),
      'ModifyServer': grpc.unary_unary_rpc_method_handler(
          servicer.ModifyServer,
          request_deserializer=nginx__pb2.ConfigServer.FromString,
          response_serializer=nginx__pb2.NginxReply.SerializeToString,
      ),
      'ModifyLB': grpc.unary_unary_rpc_method_handler(
          servicer.ModifyLB,
          request_deserializer=nginx__pb2.ConfigLB.FromString,
          response_serializer=nginx__pb2.NginxReply.SerializeToString,
      ),
      'ProcessAlerts': grpc.unary_unary_rpc_method_handler(
          servicer.ProcessAlerts,
          request_deserializer=nginx__pb2.AlertMessage.FromString,
          response_serializer=nginx__pb2.NginxReply.SerializeToString,
      ),
  }
  generic_handler = grpc.method_handlers_generic_handler(
      'nginx.Controller', rpc_method_handlers)
  server.add_generic_rpc_handlers((generic_handler,))
