import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

class SpotCurve:
    def __init__(self, file_name): #Основной конструкттор от имени входного файла
        self.data = pd.read_excel(file_name) #работать с данными в виде датафрейма удобно.

        if len(self.data) == 0: #пустой датасет не подходит
            raise ValueError('Empty dataset')

        expected_cols = ['Tenor', 'Rate', 'Maturity', 'Settlement_Date']
        for col in expected_cols:
            if col not in self.data.columns: #проверим что входной файл содержит хотя бы все нужные колонки
                raise ValueError('Invalid dataset columns')

        if len(self.data['Settlement_Date'].drop_duplicates()) != 1:
            raise ValueError('Rates from different dates are provided')

        self._settlement_date = self.data['Settlement_Date'][0] #для удобства сохраним эту дату отдельно

        #При чтении pd.read_excel стаавка должна сразу считается как число, даты начала и погашения - как даты
        #Преобразование типов может не произойти по умолчанию(возможно зависит от версии pandas,
        #поэтому на всякий случай попробуем преобразовать типы вручную)

        if (self.data['Rate'].dtype != 'float64'):
            try:
                self.data['Rate'].apply(lambda x: float(str(x).replace(',', '.'))) #не всегда входные данные с запятой вместо точки корректно преобразуются в float
            except:
                raise TypeError('Invalid rate type') #если не получилось преобразовать к дате нужного формата, значит неверный типп

        self.data['Rate'] = self.data['Rate'] / 100

        date_cols = ['Maturity', 'Settlement_Date']
        for date_col in date_cols:
            if (self.data[date_col].dtype != 'datetime64[ns]'):
                try:
                    self.data.loc[:, date_col] = pd.to_datetime(self.data.loc[:, 'date_col'], format = '%d.%m.%Y')
                except:
                    raise TypeError('Invalid date type') #если не получилось преобразовать к дате нужного формата, значит неверный тип

        self.data.loc[:, 'tenor_in_days'] = self.data.loc[:, 'Tenor'].apply(self.get_tenor_in_days) #Создадим столбец со сроком по дням

        #Теперь можем интерполировать кривую спот-ставок. Сделаем это просто с помощью numpy.interp
        #Поскольку мы лишь интерполируем кривую (а не экстрополируем), мы можем сделать это лишь в диапазоне от минимального до максимального сроков
        #Минимальным интересующим сроком будем считать 1 день, поэтому интерполяцию проведем с точностью до 1 дня

        self.min_tenor_in_days = self.data['tenor_in_days'].min()
        self.max_tenor_in_days = self.data['tenor_in_days'].max()

        self._all_tenors_in_days = [i for i in range(self.min_tenor_in_days, self.max_tenor_in_days + 1)] #все интересующие нас сроки

        #Для корректной интерполяции аргументы функции должны возрастать, позаботимся об этом
        self.data = self.data.sort_values(by = 'tenor_in_days')

        #Интерполируем ставки и сохраним их как словарь с ключами - сроками в днях
        self.spot_rates = dict(zip(self._all_tenors_in_days, np.interp(self._all_tenors_in_days, self.data['tenor_in_days'], self.data['Rate'])))



    def get_tenor_in_days(self, tenor): #Преобразует данные из столбца срока Tenor в количество дней
        #Будем предполагать, что срок дан либо в месяца MO, либо в годах YR
        if tenor.find('MO') == -1 and tenor.find('YR') == -1:
            raise ValueError('Unsupported tenor')
        tenor = tenor.strip()
        if tenor[tenor.find(' ') + 1:] == 'MO': #все, что после пробела - указывает размерность срока
            return int(tenor[:tenor.find(' ')]) * 30 #До пробела - количество месяцев. Для простоты будем считать что в каждом месяце 30 дней
        else:
            return int(tenor[:tenor.find(' ')]) * 365 #Иначе это года



    def get_spot_rate_days(self, tenor_in_days):
        if tenor_in_days < self.min_tenor_in_days:
            raise ValueError('Too small tenor value')
        if tenor_in_days > self.max_tenor_in_days:
            raise ValueError('Too big tenor value')
        return self.spot_rates[tenor_in_days]

    def get_spot_rate(self, tenor):
        tenor_in_days = self.get_tenor_in_days(tenor)
        return self.get_spot_rate_days(tenor_in_days)

    def plot_spot_curve(self):
        plt.figure(figsize = (10, 8))
        plt.title('Interpolated Spot Curve')
        plt.xlabel('Tenor')
        plt.ylabel('Rate')
        plt.plot(self._all_tenors_in_days, list(self.spot_rates.values()), color = 'royalblue', label = 'interpolated')
        plt.plot(self.data['tenor_in_days'], self.data['Rate'], 'r.', label = 'given rates')
        plt.xticks(self.data['tenor_in_days'], labels = self.data['Tenor'], rotation = 75)
        plt.show()

####################################

class ForwardCurve(SpotCurve):
    def __init__(self, file_name, future_date): #future_date - дата для которой будут рассчитываться форвардные ставки
        SpotCurve.__init__(self, file_name)
        if type(future_date) == type(str()): #на вход может быть дана дата в виде строки или непосредственно даты
            try:
                future_date = pd.to_datetime(future_date, format = '%d.%m.%Y')
            except:
                raise TypeError('Invalid date provided')
        if type(future_date) != type(pd.to_datetime('15.07.2021', format = '%d.%m.%Y')): #немного костыльная проверка на то, что на вход дана нормальная дата
            raise TypeError('Invalid date provided')
        self._future_date = future_date
        self._t_days = (self._future_date - self._settlement_date).days #момент времени t для которого ведется расчет форвардной ставки

        if self._t_days < self.min_tenor_in_days:
            raise ValueError('Too small future date to calculate any forward rates')

        if self._t_days > self.max_tenor_in_days:
            raise ValueError('Too late future date to calculate any forward rates')

        self._forward_min_tenor_in_days = max(1, self.min_tenor_in_days - self._t_days)
        self._forward_max_tenor_in_days = self.max_tenor_in_days - self._t_days

        self._all_forward_tenors = [i for i in range(self._forward_min_tenor_in_days, self._forward_max_tenor_in_days + 1)]

        self._forward_rates = dict(zip(self._all_forward_tenors, map(self.get_forward_rate_days, self._all_forward_tenors))) #Вычислим форвардные ставки по всем срокам


    def get_forward_rate_days(self, tenor_in_days):
        if tenor_in_days < self._forward_min_tenor_in_days:
            raise ValueError('Too small tenor for forward rate calculation')
        if tenor_in_days > self._forward_max_tenor_in_days:
            raise ValueError('Too big tenor for forward rate calculation provided')

        #В условии задачи не было явно сказано, соответствуют ли указанные процентные ставки простому, сложному или непрерывному способу начисления процентов.
        #Будем трактовать значения ставок таким образом, что конечная сумма, получаемая при размещении депозита на сумму 1 под указанную ставку r на срок T вычисляется по формуле
        #   (1 + r)^T. Где T - это срок выраженный в годах. Если нам задан срок в днях Days, то будем считать T = Days/365

        #Форвардные ставки будем вычислять следующим образом. Они могут быть найдены из следующего уравнения, где t - момент времени для которого мы вычисляем форвардную ставку
        #r_s - спот ставка, r_f - форвардная ставка, T - срок депозита (или кредита). Так же пусть t_0 - текущий момент времени
        #Форвардная ставка должна принимать такое значение, что размещение депозита под действующую спот ставку на срок (t + T) должно полностью соответствовать
        #размещению сначала депозита на срок t под соответствующую спот ставку, затем размщение полученной суммы на срок T под форвардную ставку. Т.е. получаем уравнение:
        #(1 + r_s_t)^t * (1 + r_f)^T = (1 + r_s_(t +T))^(t + T)     Откуда:
        #(1 + r_f)^T = (1 + r_s_(t +T))^(t + T)/(1 + r_s_t)^t
        #r_f = ( (1 + r_s_(t +T))^(t + T)/(1 + r_s_t)^t)^(1/T) - 1

        return ((1 + self.spot_rates[self._t_days + tenor_in_days])**((self._t_days + tenor_in_days)/365) / (1 + self.spot_rates[self._t_days])**(self._t_days/365))**(1/(tenor_in_days/365)) - 1


    def get_forward_rate(self, tenor): #Рассчитывает процентную ставку для указанного срока для даты указанной при создании объекта класса
        tenor_in_days = self.get_tenor_in_days(tenor)
        return self.get_forward_rate_days(tenor_in_days)


    def plot_forward_curve(self):
        plt.figure(figsize = (10, 8))
        plt.title('Forward Curve for date ' + str(self._future_date.strftime("%d.%m.%Y")))
        plt.xlabel('Tenor in days')
        plt.ylabel('Rate')
        plt.plot(self._all_forward_tenors, list(self._forward_rates.values()), color = 'royalblue')
        plt.legend()
        plt.show()

####################################

class DiscountCurve(SpotCurve):
    def __init__(self, file_name):
        SpotCurve.__init__(self, file_name)

        #Дисконтная кривая - кривая стоимостей бескупонных облигаций с соответствующими ставкой и сроком до погашения (т.е. это суммы, необходимые для размещения на депозите, чтобы в результате получить сумму 1)
        #С учетом приведенной выше формулы о сумме, получаемой при размещении 1 под ставку r на срок T, дисконтное значение d вычисляется по формуле:
        #d = 1/(1 + r)^T

        self._discount_rates = dict(zip(self._all_tenors_in_days, map(lambda x: 1/(1 + x[1])**(x[0] / 365), self.spot_rates.items())))


    def get_discount_rate_days(self, tenor_in_days):
        if tenor_in_days < self.min_tenor_in_days:
            raise ValueError('Too small tenor value')
        if tenor_in_days > self.max_tenor_in_days:
            raise ValueError('Too big tenor value')
        return self._discount_rates[tenor_in_days]


    def get_discount_rate(self, tenor):
        tenor_in_days = self.get_tenor_in_days(tenor)
        return self.get_discount_rate_days(tenor_in_days)


    def plot_discount_curve(self):
        plt.figure(figsize = (10, 8))
        plt.title('Discount Curve')
        plt.xlabel('Tenor')
        plt.ylabel('Discount rate (zero-coupon bond price)')
        plt.plot(self._all_tenors_in_days, list(self._discount_rates.values()), color = 'royalblue')
        plt.xticks(self.data['tenor_in_days'], labels = self.data['Tenor'], rotation = 75)
        plt.show()
