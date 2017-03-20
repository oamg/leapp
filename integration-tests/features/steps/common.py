from behave import given, when, then

@given("the local virtual machines")
def create_local_machines(context):
    context.machines = machines = {}
    for vm_name, image_name, playbook in context.table:
        msg = "TODO: create VM instance from {} and register as {}"
        print(msg.format(image_name, vm_name))
        machines[vm_name] = image_name

@when("{source_vm} is redeployed to {target_vm} as a macrocontainer")
def redeploy_vm_as_macrocontainer(context, source_vm, target_vm):
    context.redeployment_source = source_vm
    context.redeployment_target = target_vm
    machines = context.machines
    source_info = machines[source_vm]
    target_info = machines[target_vm]
    msg = "TODO: redeploy {} as macrocontainer on {}"
    print(msg.format(source_vm, target_vm))

@then("the HTTP responses on port {tcp_port} should match")
def check_http_responses_match(context, tcp_port):
    msg = "TODO: get HTTP response from {}:{}"
    print(msg.format(context.redeployment_source, tcp_port))
    print(msg.format(context.redeployment_target, tcp_port))
    print("TODO: Check responses match")
