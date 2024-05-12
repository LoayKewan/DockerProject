from pathlib import Path
from matplotlib.image import imread, imsave
import random

def rgb2gray(rgb):
    r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]
    gray = 0.2989 * r + 0.5870 * g + 0.1140 * b
    return gray


class Img:

    def __init__(self, path):
        """
        Do not change the constructor implementation
        """
        self.path = Path(path)
        self.data = rgb2gray(imread(path)).tolist()

    def save_img(self):
        """
        Do not change the below implementation
        """
        new_path = self.path.with_name(self.path.stem + '_filtered' + self.path.suffix)
        imsave(new_path, self.data, cmap='gray')
        return new_path

    def blur(self, blur_level=16):

        height = len(self.data)
        width = len(self.data[0])
        filter_sum = blur_level ** 2

        result = []
        for i in range(height - blur_level + 1):
            row_result = []
            for j in range(width - blur_level + 1):
                sub_matrix = [row[j:j + blur_level] for row in self.data[i:i + blur_level]]
                average = sum(sum(sub_row) for sub_row in sub_matrix) // filter_sum
                row_result.append(average)
            result.append(row_result)

        self.data = result

    def contour(self):
        for i, row in enumerate(self.data):
            res = []
            for j in range(1, len(row)):
                res.append(abs(row[j-1] - row[j]))

            self.data[i] = res

    def rotate(self):

        # TODO remove the `raise` below, and write your implementation
        from PIL import Image


        image_width = len(self.data[0])
        image_height = len(self.data)

        # Create a grayscale image from the data
        image = Image.new('L', (image_width, image_height))
        image.putdata(sum(self.data, []))

        # Rotate the image by 90 degrees
        rotated_image = image.rotate(90)

        self.data = rotated_image


    def salt_n_pepper(self):
        # TODO remove the `raise` below, and write your implementation
        rows = len(self.data)
        columns = len(self.data[0])
        for i in range(rows):
            for j in range(columns):
                ran_num = random.random()
                if ran_num < 0.2:
                    self.data[i][j] = 255
                elif ran_num > 0.8:
                    self.data[i][j] = 0

    def concat(self, other_img, direction='horizontal'):
        # TODO remove the `raise` below, and write your implementation
        raise NotImplementedError()

    def segment(self):
        # TODO remove the `raise` below, and write your implementation
        raise NotImplementedError()