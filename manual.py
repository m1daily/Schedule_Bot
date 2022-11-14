# 手動実行用
import PySimpleGUI as sg
import subprocess


sg.theme("SystemDefaultForReal")
layout = [[sg.Text('1.テキスト入力 [必須]', font=('游ゴシック',12))],
          [sg.Input(font=('游ゴシック',12))],
          [sg.Text('2.画像選択(1～4枚) [任意]', font=('游ゴシック',12))],
          [sg.FilesBrowse('ファイルを追加', key='-FILES-', file_types=(('画像ファイル', '*.jpg'), ('画像ファイル', '*.png')))],
          [sg.Text('3.送信先選択(最低1つ)', font=('游ゴシック',12))],
          [sg.OK()]]

window = sg.Window('Schedule_Bot', layout)

event, values = window.read()
window.close()
