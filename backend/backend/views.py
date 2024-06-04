import datetime
from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from users.models import CustomUser
from .models import Machine, Maintenance, Complaint, MachineModelReference, EngineModelReference, \
    TransmissionModelReference, DrivingBridgeModelReference, ControlledBridgeModelReference


@api_view(['GET'])
def get_machine_data(request):
    factory_number = request.GET.get('factory_number')
    if not factory_number:
        return Response(status=status.HTTP_400_BAD_REQUEST)

    try:
        machine = Machine.objects.get(factory_number=factory_number)
    except Machine.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    result = {
        'Зав. № машины': factory_number,
        'Модель машины': machine.machine_model.name,
        'Модель двигателя': machine.engine_model.name,
        'Зав. № двигателя': machine.engine_number,
        'Модель трансмиссии': machine.transmission_model.name,
        'Зав. № трансмиссии': machine.transmission_number,
        'Модель ведущего моста': machine.driving_bridge_model.name,
        'Зав. № ведущего моста': machine.driving_bridge_number,
        'Модель управляемого моста': machine.controlled_bridge_model.name,
        'Зав. № управляемого моста': machine.controlled_bridge_number
    }

    authenticated_data = {}

    try:
        if request.user == machine.client or request.user.role in ['service_organisation', 'manager']:
            authenticated_data = {
                'Договор поставки №, дата': machine.delivery_contract,
                'Дата отгрузки с завода': machine.date_of_shipment.strftime("%d.%m.%Y"),
                'Грузополучатель (конечный потребитель)': machine.consignee,
                'Адрес поставки (эксплуатации)': machine.delivery_address,
                'Комплектация (доп. опции)': machine.complete_set,
                'Клиент': machine.client.first_name,
                'Cервисная компания': machine.service_company.first_name,
            }
    except AttributeError:
        pass

    result.update(authenticated_data)
    return Response(result)


@api_view(['POST'])
def post_machine_data(request):
    if not request.user.is_authenticated or request.user.role != 'manager':
        return Response(status=status.HTTP_403_FORBIDDEN, data={'result': 'Ошибка доступа'})

    required_keys = ['Зав. № машины', 'Модель машины', 'Модель двигателя', 'Зав. № двигателя',
                     'Модель трансмиссии', 'Зав. № трансмиссии', 'Модель ведущего моста',
                     'Зав. № ведущего моста', 'Модель управляемого моста', 'Зав. № управляемого моста',
                     'Договор поставки №, дата', 'Дата отгрузки с завода', 'Грузополучатель (конечный потребитель)',
                     'Адрес поставки (эксплуатации)', 'Комплектация (доп. опции)', 'Клиент', 'Cервисная компания']

    for key in required_keys:
        if key not in request.data:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'result': f'Отсутствует обязательный ключ в запросе: {key}'})

    try:
        factory_number = request.data['Зав. № машины']
        machine_model, _ = MachineModelReference.objects.get_or_create(name=request.data['Модель машины'])
        engine_model, _ = EngineModelReference.objects.get_or_create(name=request.data['Модель двигателя'])
        engine_number = request.data['Зав. № двигателя']
        transmission_model, _ = TransmissionModelReference.objects.get_or_create(name=request.data['Модель трансмиссии'])
        transmission_number = request.data['Зав. № трансмиссии']
        driving_bridge_model, _ = DrivingBridgeModelReference.objects.get_or_create(name=request.data['Модель ведущего моста'])
        driving_bridge_number = request.data['Зав. № ведущего моста']
        controlled_bridge_model, _ = ControlledBridgeModelReference.objects.get_or_create(name=request.data['Модель управляемого моста'])
        controlled_bridge_number = request.data['Зав. № управляемого моста']
        delivery_contract = request.data['Договор поставки №, дата']
        date_of_shipment = datetime.datetime.strptime(request.data['Дата отгрузки с завода'], "%d.%m.%Y")
        consignee = request.data['Грузополучатель (конечный потребитель)']
        delivery_address = request.data['Адрес поставки (эксплуатации)']
        complete_set = request.data['Комплектация (доп. опции)']
        client = CustomUser.objects.get(first_name=request.data['Клиент'])
        service_company = CustomUser.objects.get(first_name=request.data['Cервисная компания'])

        machine, created = Machine.objects.update_or_create(
            factory_number=factory_number,
            defaults={
                'machine_model': machine_model,
                'engine_model': engine_model,
                'engine_number': engine_number,
                'transmission_model': transmission_model,
                'transmission_number': transmission_number,
                'driving_bridge_model': driving_bridge_model,
                'driving_bridge_number': driving_bridge_number,
                'controlled_bridge_model': controlled_bridge_model,
                'controlled_bridge_number': controlled_bridge_number,
                'delivery_contract': delivery_contract,
                'date_of_shipment': date_of_shipment,
                'consignee': consignee,
                'delivery_address': delivery_address,
                'complete_set': complete_set,
                'client': client,
                'service_company': service_company,
            }
        )
        if created:
            result = f'Успешно создана новая машина {factory_number}!'
        else:
            result = f'Успешно обновлены данные машины {factory_number}!'
        return Response(status=status.HTTP_200_OK, data={'result': result})

    except Exception as e:
        print(e)
        result = f'Ошибка обновления данных машины, перепроверьте данные!'
    return Response(status=status.HTTP_400_BAD_REQUEST, data={'result': result})


@api_view(['GET'])
def get_machine_list(request):
    if not request.user.is_authenticated:
        return Response(status=status.HTTP_403_FORBIDDEN, data={'result': 'Ошибка доступа'})

    factory_number_filer = request.GET.get('factory_number', '')
    machine_model_filer = request.GET.get('machine_model', 'Все модели')
    engine_model_filer = request.GET.get('engine_model', 'Все модели')
    transmission_model_filer = request.GET.get('transmission_model', 'Все модели')
    driving_bridge_model_filer = request.GET.get('driving_bridge_model', 'Все модели')
    controlled_bridge_model = request.GET.get('controlled_bridge_model', 'Все модели')

    machine_list = Machine.objects.all()

    if factory_number_filer:
        machine_list = machine_list.filter(factory_number__contains=factory_number_filer)

    if machine_model_filer != "Все модели":
        machine_list = machine_list.filter(machine_model__name=machine_model_filer)

    if engine_model_filer != "Все модели":
        machine_list = machine_list.filter(engine_model__name=engine_model_filer)

    if transmission_model_filer != "Все модели":
        machine_list = machine_list.filter(transmission_model__name=transmission_model_filer)

    if driving_bridge_model_filer != "Все модели":
        machine_list = machine_list.filter(driving_bridge_model__name=driving_bridge_model_filer)

    if controlled_bridge_model != "Все модели":
        machine_list = machine_list.filter(controlled_bridge_model__name=controlled_bridge_model)

    data = {
        'machine_list_data': machine_list.values(
            'id',
            'factory_number',
            'machine_model__name',
            'engine_model__name',
            'transmission_model__name',
            'driving_bridge_model__name',
            'controlled_bridge_model__name'
        ),
        'filter_data': {
            'machine_models': MachineModelReference.objects.all().values('name'),
            'engine_models': EngineModelReference.objects.all().values('name'),
            'transmission_models': TransmissionModelReference.objects.all().values('name'),
            'driving_bridge_models': DrivingBridgeModelReference.objects.all().values('name'),
            'controlled_bridge_models': ControlledBridgeModelReference.objects.all().values('name'),
        }
    }

    return Response(status=status.HTTP_200_OK, data=data)


@api_view(['GET'])
def get_maintenance(request):
    if not request.user.is_authenticated or request.user.role not in ['service_organisation', 'manager']:
        return Response(status=status.HTTP_403_FORBIDDEN, data={'result': 'Ошибка доступа'})

    factory_number = request.GET.get('factory_number', '')

    maintenances = Maintenance.objects.filter(machine__factory_number=factory_number)
    result = []

    for maintenance in maintenances:
        result.append({
            'id': maintenance.id,
            'Вид ТО': maintenance.type_of_maintenance.name,
            'Дата проведения': maintenance.date_of_maintenance.strftime("%d.%m.%Y"),
            'Наработка, м/час': maintenance.operating_time,
            '№ заказ-наряда': maintenance.order_number,
            'Дата заказ-наряда': maintenance.order_date.strftime("%d.%m.%Y"),
            'Машина': maintenance.machine.factory_number,
        })

    return Response(status=status.HTTP_200_OK, data=result)


@api_view(['GET'])
def get_complaints(request):
    if not request.user.is_authenticated or request.user.role not in ['service_organisation', 'manager']:
        return Response(status=status.HTTP_403_FORBIDDEN, data={'result': 'Ошибка доступа'})

    factory_number = request.GET.get('factory_number', '')

    complaints = Complaint.objects.filter(machine__factory_number=factory_number)
    result = []

    for complaint in complaints:
        result.append({
            'id': complaint.id,
            'Дата отказа': complaint.date_of_refusal.strftime("%d.%m.%Y"),
            'Наработка, м/час': complaint.operating_time,
            'Узел отказа': complaint.failure_node.name,
            'Описание отказа': complaint.failure_description,
            'Способ восстановления': complaint.recovery_method.name,
            'Используемые запасные части': complaint.parts_used,
            'Дата восстановления': complaint.date_of_restoration.strftime("%d.%m.%Y"),
            'Время простоя техники': complaint.get_equipment_downtime(),
            'Машина': complaint.machine.factory_number
        })

    return Response(status=status.HTTP_200_OK, data=result)
