"""
设备模板定义
每种设备类型包含：名称、字段列表、OCR 策略、CSV 文件名
"""
templates = {
    "chiller": {
        "name": "励磁冷却系统",
        "title": "苏州苏试试验集团股份有限公司励磁冷却系统",
        "group_title": "励磁冷却系统",
        "csv": "records_chiller.csv",
        "ocr_strategy": "position_sort",
        "fields": [
            ("flow_main",    "开式水塔输出流量", "L/Min"),
            ("temp_main",    "开式水塔输出水温", "°C"),
            ("conductivity", "电导率",           "us/cm"),
            ("temp_in",      "温度(输入回路)",    "°C"),
            ("pressure",     "压力",              "bar"),
            ("flow_out",     "流量(输出回路)",    "L/Min"),
            ("temp_out",     "温度(输出回路)",    "°C"),
        ],
    },
    "circulating": {
        "name": "循环水系统（三九制冷）",
        "title": "无锡三九制冷设备有限公司 循环水系统",
        "group_title": "循环水系统",
        "csv": "records_circulating.csv",
        "ocr_strategy": "label_match",
        "fields": [
            ("temp_in_1",    "1#进水温度", "°C"),
            ("temp_out_1",   "1#出水温度", "°C"),
            ("temp_in_2",    "2#进水温度", "°C"),
            ("temp_out_2",   "2#出水温度", "°C"),
            ("tank_hot",     "水箱热水侧温度", "°C"),
            ("tank_cold",    "水箱冷水侧温度", "°C"),
            ("freq_1f_a",    "1楼A泵频率", "Hz"),
            ("freq_1f_b",    "1楼B泵频率", "Hz"),
            ("press_1f",     "1楼出水压力", "Bar"),
            ("freq_2f_a",    "2楼A泵频率", "Hz"),
            ("freq_2f_b",    "2楼B泵频率", "Hz"),
            ("press_2f",     "2楼出水压力", "Bar"),
            ("curr_pump_1",  "1#自循环泵电流", "A"),
            ("curr_pump_2",  "2#自循环泵电流", "A"),
            ("curr_pump_3",  "3#自循环泵电流", "A"),
            ("curr_1f_a",    "1楼A循环泵电流", "A"),
            ("curr_1f_b",    "1楼B循环泵电流", "A"),
            ("curr_2f_a",    "2楼A循环泵电流", "A"),
            ("curr_2f_b",    "2楼B循环泵电流", "A"),
        ],
    },
}
