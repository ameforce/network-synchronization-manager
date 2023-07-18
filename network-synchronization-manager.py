from multiprocessing import Pool
from datetime import datetime
from tqdm import tqdm
import multiprocessing
import subprocess
import paramiko
import shutil
import time
import os


class NetworkSynchronizationManager:
    def __init__(self):
        self.interval_time = 5 * 60
        self.__connect_method_list, self.__connect_method = ['ssh', 'copy'], ''
        self.__path_dict = {'src_path': '', 'dst_path': ''}
        self.__file_list, self.__src_file_list, self.__dst_file_list = [], [], []
        self.__file_dict, self.__src_file_dict, self.__dst_file_dict = {}, {}, {}
        self.__replace_file_dict = {}

    def __initializing_connect_method(self) -> None:
        self.__connect_method = ''

    def __initializing_path(self) -> None:
        for path_kind in self.__path_dict:
            self.__path_dict[path_kind] = ''

    def __initializing_file(self) -> None:
        self.__file_list = []
        self.__file_dict = {}

    def __initializing_need_file(self) -> None:
        self.__replace_file_dict = {}

    def __validate_selection(self, selection: str) -> None:
        try:
            number = int(selection)
        except ValueError as e:
            raise ValueError('A non-numeric string was entered.\nPlease enter a number again.')
        if number <= 0 or number > len(self.__connect_method_list):
            raise ValueError('A number was entered that is out of range.\nPlease enter a number again.')

    def __validate_path(self, path: str, connect_method: str) -> None:
        # Todo: Need to determine if it's a network or localhost path based on the state of connect_method and path.
        # Todo: If it's a network path, need to develop logic to determine if it actually exists.
        if not os.path.exists(path):
            raise ValueError('A path that does not exist or is inaccessible.\nPlease enter a different path again.')
        for path_kind in self.__path_dict:
            if self.__path_dict[path_kind] == path:
                raise ValueError('The paths in src_path and dst_path cannot be the same. This could be a logical error '
                                 'or use excessive resources.\nPlease enter a different path again.')

    def __set_path(self) -> None:
        self.__initializing_connect_method()
        self.__initializing_path()
        print(f'Enter the way you want to connect.')
        while True:
            for i in range(len(self.__connect_method_list)):
                print(f'{i+1}. {self.__connect_method_list[i]}')
            selection = input('--> ')
            try:
                self.__validate_selection(selection)
            except ValueError as e:
                print(f'\n\n{e}')
                continue
            self.__connect_method = self.__connect_method_list[int(selection)-1]
            print(self.__connect_method)
            break
        for path_kind in self.__path_dict:
            print(f'Enter the {path_kind} you want to monitor.')
            if self.__connect_method == 'ssh' and path_kind == 'dst_path':
                print(f'WARNING: It must be accessible via SSH')
            while True:
                path = input('--> ')
                try:
                    self.__validate_path(path, self.__connect_method)
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

    @staticmethod
    def __copy_file(src_file: str, dst_file: str, progress: tqdm) -> None:
        shutil.copy2(src_file, dst_file)

    def __file_transfer(self):
        # Todo: requires development
        pool = Pool(processes=8)
        progress_list = []
        process_list = []
        for src_file in self.__replace_file_dict:
            dst_file = self.__replace_file_dict[src_file]
            command = f'copy "{src_file}" "{dst_file}"'
            print(f'command: {command}')
            progress = tqdm(total=os.path.getsize(src_file), unit='bytes', unit_scale=True)
            progress_list.append(progress)
            process_list.append(pool.apply_async(self.__copy_file, args=(src_file, dst_file, progress)))
        pool.close()
        while not all([process.ready() for process in process_list]):
            for progress in progress_list:
                progress.update()
            continue
        print(f'FINISH: ~~')
        for progress in progress_list:
            progress.close()
        return

    def logic(self) -> None:
        print('Path set and validation...', end='')
        self.__set_path()
        print('Complete')
        while True:
            self.__initializing_file()
            print('Getting list of files in src_path...', end='')
            self.__src_file_list = self.__get_file_list(self.__path_dict['src_path'])
            self.__src_file_dict = self.__get_file_time_data(self.__file_list)
            print('Complete')
            self.__initializing_file()
            print('Getting list of files in dst_path...', end='')
            self.__dst_file_list = self.__get_file_list(self.__path_dict['dst_path'])
            self.__dst_file_dict = self.__get_file_time_data(self.__file_list)
            print('Complete')
            self.__initializing_need_file()
            print('Determining the list of files to update...', end='')
            self.__determine_latest(self.__src_file_dict, self.__dst_file_dict)
            print('Complete')
            print('Transferring files...', end='')
            self.__file_transfer() # Todo: requires development
            print('Complete')
            self.__initializing_file()
            self.__initializing_need_file()
            time.sleep(self.interval_time)


if __name__ == '__main__':
    nsm = NetworkSynchronizationManager()
    nsm.logic()
