from Curves import SpotCurve, ForwardCurve, DiscountCurve
import unittest

class TestSpotCurve(unittest.TestCase):
    def test_spot_rates(self):
        spot = SpotCurve('Rates_2021_07_14.xlsx')
        self.assertTrue(abs(spot.get_spot_rate('4 MO') - 0.0688047) < 0.0000001) #Поскольку работаем с дробными числами - будем сравнивать их с заданной точностью
        self.assertTrue(abs(spot.get_spot_rate('7 MO') - 0.0736081) < 0.0000001)
        self.assertTrue(abs(spot.get_spot_rate_days(100) - 0.0674253) < 0.0000001)
        self.assertTrue(abs(spot.get_spot_rate_days(3211) - 0.0706677) < 0.0000001)

    def test_spot_exceptions(self):
        spot = SpotCurve('Rates_2021_07_14.xlsx')
        self.assertRaises(ValueError, spot.get_spot_rate, '1 MO') #Слишком маленький срок
        self.assertRaises(ValueError, spot.get_spot_rate, '11 YR') #Слишком большой срок
        self.assertRaises(ValueError, spot.get_spot_rate, '11 asdasd') #Некорректный ввод
        self.assertRaises(ValueError, spot.get_spot_rate_days, 30) #Слишком маленький срок
        self.assertRaises(ValueError, spot.get_spot_rate_days, 30000) #Слишком большой срок

class TestForwardCurve(unittest.TestCase):
    def test_forward_rates(self):
        forward = ForwardCurve('Rates_2021_07_14.xlsx', '15.10.2021')
        self.assertTrue(abs(forward.get_forward_rate('1 MO') - 0.0754513) < 0.0000001)
        self.assertTrue(abs(forward.get_forward_rate('4 MO') - 0.0789212) < 0.0000001) #Поскольку работаем с дробными числами - будем сравнивать их с заданной точностью
        self.assertTrue(abs(forward.get_forward_rate('7 MO') - 0.0784670) < 0.0000001)
        self.assertTrue(abs(forward.get_forward_rate_days(100) - 0.079112851) < 0.0000001)
        self.assertTrue(abs(forward.get_forward_rate_days(3211) - 0.07077973) < 0.0000001)

    def test_forward_exceptions_init(self):
        self.assertRaises(ValueError, ForwardCurve, 'Rates_2021_07_14.xlsx', '15.07.2021') #Слишком близкий срок для расчета форвардной ставки
        self.assertRaises(ValueError, ForwardCurve, 'Rates_2021_07_14.xlsx', '01.07.2101') #Слишком дальний срок для расчета форвардной ставки

    def test_forward_exceptions(self):
        forward = ForwardCurve('Rates_2021_07_14.xlsx', '15.10.2021')
        self.assertRaises(ValueError, forward.get_forward_rate, '11 YR') #Слишком большой срок
        self.assertRaises(ValueError, forward.get_forward_rate, 'asd') #Некорректный ввод
        self.assertRaises(ValueError, forward.get_forward_rate_days, 0) #Слишком маленький срок
        self.assertRaises(ValueError, forward.get_forward_rate_days, 30000) #Слишком большой срок

class TestDiscountCurve(unittest.TestCase):
    def test_discount_rates(self):
        discount = DiscountCurve('Rates_2021_07_14.xlsx')
        self.assertTrue(abs(discount.get_discount_rate('3 MO') - 0.9841966) < 0.0000001) #Поскольку работаем с дробными числами - будем сравнивать их с заданной точностью
        self.assertTrue(abs(discount.get_discount_rate('7 MO') - 0.9599599) < 0.0000001)
        self.assertTrue(abs(discount.get_discount_rate_days(100) - 0.9822822) < 0.0000001)
        self.assertTrue(abs(discount.get_discount_rate_days(3211) - 0.5484281) < 0.0000001)

    def test_discount_exceptions(self):
        discount = DiscountCurve('Rates_2021_07_14.xlsx')
        self.assertRaises(ValueError, discount.get_discount_rate, '11 YR') #Слишком большой срок
        self.assertRaises(ValueError, discount.get_discount_rate, 'asd') #Некорректный ввод
        self.assertRaises(ValueError, discount.get_discount_rate_days, 15) #Слишком маленький срок
        self.assertRaises(ValueError, discount.get_discount_rate_days, 30000) #Слишком большой срок
