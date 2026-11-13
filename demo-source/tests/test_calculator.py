import unittest
from calculator import descuento, subtotal, total_final


class CalculadoraTest(unittest.TestCase):
    def test_subtotal(self):
        self.assertEqual(subtotal(10, 3), 30)

    def test_descuento(self):
        self.assertEqual(descuento(100, True), 10)
        self.assertEqual(descuento(100, False), 0)

    def test_total_final(self):
        self.assertEqual(total_final(10, 3, True), 27)
        self.assertEqual(total_final(10, 3, False), 30)


if __name__ == '__main__':
    unittest.main()
