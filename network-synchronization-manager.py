from datetime import datetime
import time
import os


class NetworkSynchronizationManager:
    def __init__(self):
        self.interval_time = 5 * 60
        self.__path_dict = {'src_path': '', 'dst_path': ''}
        self.__file_list, self.__src_file_list, self.__dst_file_list = [], [], []
        self.__file_dict, self.__src_file_dict, self.__dst_file_dict = {}, {}, {}
        self.__replace_file_dict = {}

    def __validate_path(self, path: str) -> bool:
        if not os.path.exists(path):
            raise ValueError('A path that does not exist or is inaccessible.\nPlease enter a different path again.')
        for path_kind in self.__path_dict:
            if self.__path_dict[path_kind] == path:
                raise ValueError('The paths in src_path and dst_path cannot be the same. This could be a logical error '
                                 'or use excessive resources.\nPlease enter a different path again.')
        return True

    def __initializing_path(self) -> None:
        for path_kind in self.__path_dict:
            self.__path_dict[path_kind] = ''

    def __initializing_file(self) -> None:
        self.__file_list = []
        self.__file_dict = {}

    def __initializing_need_file(self) -> None:
        self.__replace_file_dict = {}

    def __set_path(self) -> None:
        self.__initializing_path()
        for path_kind in self.__path_dict:
            print(f'Enter the {path_kind} you want to monitor.')
            while True:
                path = input('--> ')
                try:
                    self.__validate_path(path)
                except ValueError as e:
                    print(f'\n\n{e}')
                    continue
                self.__path_dict[path_kind] = path
                break

    def __get_file_list(self, path: str) -> list[str]:
        # Todo: Change to handle multithreading at a later date.
        file_list = os.listdir(path)
        for name in file_list:
            combine_path = os.path.join(path, name)
            if os.path.isfile(combine_path):
                self.__file_list.append(combine_path)
            else:
                self.__get_file_list(combine_path)
        return self.__file_list

    def __get_file_time_data(self, file_list: list[str]) -> dict[str, str]:
        for file in file_list:
            self.__file_dict[file] = datetime.fromtimestamp(os.path.getmtime(file))
        return self.__file_dict

    def __determine_latest(self, src_time_dict: dict[str, str], dst_time_dict: dict[str, str]) -> dict[str, str]:
        self.__initializing_need_file()
        for src_key in src_time_dict:
            is_duplication = False
            src_basename = os.path.basename(src_key)
            for dst_key in dst_time_dict:
                dst_basename = os.path.basename(dst_key)
                if src_basename == dst_basename:
                    is_duplication = True
                    if src_time_dict[src_key] > dst_time_dict[dst_key]:
                        self.__replace_file_dict[src_key] = os.path.join(self.__path_dict['dst_path'], dst_basename)
                    break
            if not is_duplication and src_key not in self.__replace_file_dict:
                self.__replace_file_dict[src_key] = os.path.join(self.__path_dict['dst_path'], src_basename)
        return self.__replace_file_dict

    def __file_transfer(self):
        # Todo: requires development
        return

    def logic(self) -> None:
        self.__set_path()
        while True:
            self.__initializing_file()
            self.__src_file_list = self.__get_file_list(self.__path_dict['src_path'])
            self.__src_file_dict = self.__get_file_time_data(self.__file_list)
            self.__initializing_file()
            self.__dst_file_list = self.__get_file_list(self.__path_dict['dst_path'])
            self.__dst_file_dict = self.__get_file_time_data(self.__file_list)
            self.__initializing_need_file()
            self.__determine_latest(self.__src_file_dict, self.__dst_file_dict)
            self.__file_transfer() # Todo: requires development
            self.__initializing_file()
            self.__initializing_need_file()
            time.sleep(self.interval_time)


if __name__ == '__main__':
    nsm = NetworkSynchronizationManager()
    nsm.logic()
