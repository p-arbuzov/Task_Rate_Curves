from Curves import SpotCurve, ForwardCurve, DiscountCurve

#Этот код выводит 3 графика кривых ставок - спот, форвард и дисконтных

spot = SpotCurve('Rates_2021_07_15.xlsx')
spot.plot_spot_curve()

forward = ForwardCurve('Rates_2021_07_15.xlsx', '20.11.2022')
forward.plot_forward_curve()

discount = DiscountCurve('Rates_2021_07_15.xlsx')
discount.plot_discount_curve()
