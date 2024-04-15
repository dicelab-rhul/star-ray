from typing import Callable
import h5py
import pathlib

from ._history import _History


class _HistoryH5Sync(_History):
    def __init__(
        self,
        path: str = "data_store.h5",
        buffer_size: int = 10000,
        flush_proportion: float = 0.5,
        force: bool = False,
        serialize: Callable = None,
        deserialize: Callable = None,
    ):
        super().__init__()
        _path = pathlib.Path(path).expanduser().resolve()
        if not force and _path.exists():
            raise FileExistsError(
                f"The file '{_path}' already exists, set `force=True` to overwrite the file."
            )
        self._path = str(_path)
        self._dataset_name = "data"
        self.buffer_size = buffer_size
        self.flush_proportion = flush_proportion
        self.init_dataset()
        self._total_items_on_disk = self.get_initial_item_count()
        if serialize is None:
            serialize = lambda x: x.encode("UTF-8")
        if deserialize is None:
            deserialize = lambda x: x.decode("UTF-8")
        self.serialize = serialize
        self.deserialize = deserialize

    def __len__(self):
        return self._total_items_on_disk + len(self.buffer)

    def get_initial_item_count(self):
        with h5py.File(self._path, "r") as file:
            return file[self._dataset_name].shape[0]  # pylint: disable=E1101

    def init_dataset(self):
        with h5py.File(self._path, "w") as file:
            file.create_dataset(
                self._dataset_name,
                (0,),
                maxshape=(None,),
                dtype=h5py.special_dtype(vlen=str),
            )

    def flush_buffer(self):
        # Calculate the number of items to flush from the buffer
        flush_count = int(len(self.buffer) * self.flush_proportion)
        # Items to be flushed to disk
        items_to_flush = self.buffer[:flush_count]

        with h5py.File(self._path, "a") as file:
            dataset = file[self._dataset_name]
            new_size = dataset.shape[0] + flush_count  # pylint: disable=E1101
            # TODO rather than just add enough space, consider a better resize scheme? for now this is ok...
            dataset.resize(new_size, axis=0)  # pylint: disable=E1101
            dataset[-flush_count:] = [self.serialize(x) for x in items_to_flush]
            self._total_items_on_disk += flush_count

        # Keep the most recent elements in the buffer
        self.buffer = self.buffer[flush_count:]

    def push(self, item):
        self.buffer.append(item)
        if len(self.buffer) >= self.buffer_size:
            self.flush_buffer()

    def __getitem__(self, index: int | slice):
        if isinstance(index, int):
            return self._get_single_item(index)
        elif isinstance(index, slice):
            return self._get_slice_items(index)
        elif index is ...:
            return self._get_all_items()
        elif isinstance(index, tuple):
            raise IndexError(f"Invalid index {index}, array is 1-dimensional.")

    def _get_all_items(self):
        with h5py.File(self._path, "r") as file:
            dataset = file[self._dataset_name]
            data = [self.deserialize(x) for x in dataset[:]]
        data.extend(self.buffer)
        return data

    def _get_slice_items(self, index: slice):
        size = self._total_items_on_disk + len(self.buffer)
        start, stop, step = index.start, index.stop, index.step
        if start is None:
            start = 0
        if stop is None:
            stop = size
        if start < 0:
            start = size + start
        if stop < 0:
            stop = size + stop
        if start >= stop:
            return []

        if start >= self._total_items_on_disk:
            return self.buffer[
                start
                - self._total_items_on_disk : stop
                - self._total_items_on_disk : step
            ]
        elif stop <= self._total_items_on_disk:
            # we are accessing only the disk
            with h5py.File(self._path, "r") as file:
                dataset = file[self._dataset_name]
                return [self.deserialize(x) for x in dataset[start:stop:step]]
        else:
            # there is some overlap...
            with h5py.File(self._path, "r") as file:
                dataset = file[self._dataset_name]
                data = [self.deserialize(x) for x in dataset[start:stop:step]]
            stop -= self._total_items_on_disk
            # it must be that start < self.total_items_on_disk, this means we take from index 0 of the buffer
            data2 = self.buffer[0:stop:step]
            data.extend(data2)
            return data

    def _get_single_item(self, index: int):
        if index < 0:
            index = self._total_items_on_disk + len(self.buffer) + index
        if index >= self._total_items_on_disk:
            buffer_index = index - self._total_items_on_disk
            # print(buffer_index)
            return self.buffer[buffer_index]
        else:
            with h5py.File(self._path, "r") as file:
                dataset = file[self._dataset_name]
                return self.deserialize(dataset[index])

    def flush_all(self):
        old_flush_proportion = self.flush_proportion
        self.flush_proportion = 1
        self.flush_buffer()
        self.flush_proportion = old_flush_proportion

    def close(self):
        self.flush_all()
