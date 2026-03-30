from __future__ import annotations

import argparse
import csv
import re
import time
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, Optional, Set, Tuple


# ==================== 前置配置区（优先修改这里） ====================
DEFAULT_DATA_DIR = Path(
	r"I:\数据\中国气候数据资料日值数据集V3.0(1950-2019)SURF_CLI_CHN_MUL_DAY_V3.0\datasets\TEM"
)
DEFAULT_STATION_ID = "55690"
DEFAULT_OUTPUT_MONTHLY = Path("错那县_55690_逐月温度.csv")
DEFAULT_OUTPUT_CLIMATOLOGY = Path("错那县_55690_多年各月平均温度.csv")
DEFAULT_TEMPERATURE_FIELD = "tem_avg"
# ==================================================================


FILE_PATTERN = re.compile(r"SURF_CLI_CHN_MUL_DAY-TEM-12001-(\d{4})(\d{2})\.TXT$", re.IGNORECASE)
TEMPERATURE_FIELD_INDEX = {
	"tem_avg": 7,
	"tem_max": 8,
	"tem_min": 9,
}


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(
		description="计算地区历年每月平均温度（基于 SURF_CLI_CHN_MUL_DAY-TEM-12001 文件）"
	)
	parser.add_argument(
		"--data-dir",
		type=Path,
		default=DEFAULT_DATA_DIR,
		help="输入目录：TEM 文件所在目录",
	)
	parser.add_argument(
		"--temperature-field",
		choices=tuple(TEMPERATURE_FIELD_INDEX.keys()),
		default=DEFAULT_TEMPERATURE_FIELD,
		help="使用哪个温度字段计算（默认 tem_avg）",
	)
	parser.add_argument(
		"--station-file",
		type=Path,
		default=None,
		help="可选：地区站点列表文件（txt/csv/xlsx），不传则使用所有站点",
	)
	parser.add_argument(
		"--station-id",
		type=str,
		default=DEFAULT_STATION_ID,
		help="可选：单台站编号（如 55690）。设置后仅计算该台站",
	)
	parser.add_argument(
		"--station-column",
		type=str,
		default=None,
		help="当 station-file 是 xlsx/csv 时，指定站号列名（不指定会自动猜测）",
	)
	parser.add_argument(
		"--output-monthly",
		type=Path,
		default=DEFAULT_OUTPUT_MONTHLY,
		help="输出逐月结果 CSV 路径",
	)
	parser.add_argument(
		"--output-climatology",
		type=Path,
		default=DEFAULT_OUTPUT_CLIMATOLOGY,
		help="输出多年各月平均结果 CSV 路径",
	)
	return parser.parse_args()


def decode_temperature(raw_value: int) -> Optional[float]:
	"""
	将 TEM 编码转换为摄氏度。

	规则（依据数据说明）：
	- 32766: 缺测 -> None
	- 其他值: 单位 0.1 摄氏度
	"""
	if raw_value == 32766:
		return None

	return raw_value / 10.0


def find_tem_files(data_dir: Path) -> Iterable[Tuple[int, int, Path]]:
	files = []
	for p in data_dir.glob("SURF_CLI_CHN_MUL_DAY-TEM-12001-*.TXT"):
		m = FILE_PATTERN.match(p.name)
		if not m:
			continue
		year = int(m.group(1))
		month = int(m.group(2))
		files.append((year, month, p))

	files.sort(key=lambda x: (x[0], x[1]))
	return files


def normalize_station_id(value: object) -> Optional[str]:
	if value is None:
		return None
	s = str(value).strip()
	if not s:
		return None

	# 兼容 xlsx 中站号被读成 float（如 50527.0）
	if s.endswith(".0") and s[:-2].isdigit():
		s = s[:-2]

	digits = "".join(ch for ch in s if ch.isdigit())
	if len(digits) >= 5:
		return digits
	return None


def read_station_ids_from_txt_or_csv(path: Path) -> Set[str]:
	station_ids: Set[str] = set()
	with path.open("r", encoding="utf-8", errors="ignore") as f:
		for line in f:
			# 同时兼容纯站号和逗号分隔格式
			parts = re.split(r"[\s,;\t]+", line.strip())
			for part in parts:
				sid = normalize_station_id(part)
				if sid:
					station_ids.add(sid)
	return station_ids


def read_station_ids_from_xlsx(path: Path, station_column: Optional[str]) -> Set[str]:
	try:
		import importlib

		openpyxl = importlib.import_module("openpyxl")
		load_workbook = openpyxl.load_workbook
	except ImportError as exc:
		raise RuntimeError(
			"读取 xlsx 需要 openpyxl，请先安装：pip install openpyxl"
		) from exc

	wb = load_workbook(path, read_only=True, data_only=True)
	ws = wb.active

	rows = ws.iter_rows(values_only=True)
	header = next(rows, None)
	if header is None:
		return set()

	header_list = [str(h).strip() if h is not None else "" for h in header]

	col_idx: Optional[int] = None
	if station_column:
		for i, name in enumerate(header_list):
			if name == station_column:
				col_idx = i
				break
		if col_idx is None:
			raise ValueError(f"xlsx 中未找到站号列: {station_column}")
	else:
		candidates = {"区站号", "站号", "station_id", "station", "站点编号"}
		for i, name in enumerate(header_list):
			if name in candidates:
				col_idx = i
				break
		if col_idx is None:
			# 自动回退到第一列
			col_idx = 0

	station_ids: Set[str] = set()
	for row in rows:
		if col_idx >= len(row):
			continue
		sid = normalize_station_id(row[col_idx])
		if sid:
			station_ids.add(sid)

	return station_ids


def load_region_station_ids(station_file: Optional[Path], station_column: Optional[str]) -> Optional[Set[str]]:
	if station_file is None:
		return None
	if not station_file.exists():
		raise FileNotFoundError(f"站点文件不存在: {station_file}")

	suffix = station_file.suffix.lower()
	if suffix in {".txt", ".csv"}:
		ids = read_station_ids_from_txt_or_csv(station_file)
	elif suffix in {".xlsx", ".xlsm"}:
		ids = read_station_ids_from_xlsx(station_file, station_column)
	else:
		raise ValueError("station-file 仅支持 txt/csv/xlsx")

	if not ids:
		raise ValueError("未从站点文件读取到任何站号")
	return ids


def process_one_file(
	file_path: Path,
	temperature_idx: int,
	station_filter: Optional[Set[str]],
) -> Dict[str, Tuple[float, int]]:
	"""返回该月每个站点的温度累计值与有效天数。"""
	station_sum_and_count: Dict[str, Tuple[float, int]] = defaultdict(lambda: (0.0, 0))

	with file_path.open("r", encoding="utf-8", errors="ignore") as f:
		for line in f:
			parts = line.split()
			if len(parts) <= temperature_idx:
				continue

			station_id = parts[0]
			if station_filter is not None and station_id not in station_filter:
				continue

			try:
				raw_value = int(parts[temperature_idx])
			except ValueError:
				continue

			temperature_c = decode_temperature(raw_value)
			if temperature_c is None:
				continue

			running_sum, running_count = station_sum_and_count[station_id]
			station_sum_and_count[station_id] = (running_sum + temperature_c, running_count + 1)

	return station_sum_and_count


def write_monthly_csv(output_path: Path, records: list[dict]) -> None:
	output_path.parent.mkdir(parents=True, exist_ok=True)
	with output_path.open("w", newline="", encoding="utf-8-sig") as f:
		writer = csv.DictWriter(
			f,
			fieldnames=[
				"year",
				"month",
				"yyyymm",
				"station_count",
				"region_avg_temperature_c",
				"source_file",
			],
		)
		writer.writeheader()
		writer.writerows(records)


def write_climatology_csv(output_path: Path, records: list[dict]) -> None:
	output_path.parent.mkdir(parents=True, exist_ok=True)
	with output_path.open("w", newline="", encoding="utf-8-sig") as f:
		writer = csv.DictWriter(
			f,
			fieldnames=[
				"month",
				"year_count",
				"climatology_avg_temperature_c",
			],
		)
		writer.writeheader()
		writer.writerows(records)


def print_progress(current: int, total: int, current_file: Path, start_time: float) -> None:
	if total <= 0:
		return

	percent = current / total * 100
	elapsed = time.time() - start_time
	eta = (elapsed / current) * (total - current) if current > 0 else 0.0
	msg = (
		f"\r处理进度: {current}/{total} ({percent:6.2f}%) "
		f"ETA: {eta:6.1f}s 当前文件: {current_file.name}"
	)
	print(msg, end="", flush=True)


def main() -> None:
	args = parse_args()
	if not args.data_dir.exists():
		raise FileNotFoundError(f"数据目录不存在: {args.data_dir}")

	station_filter = load_region_station_ids(args.station_file, args.station_column)
	if args.station_id is not None:
		normalized = normalize_station_id(args.station_id)
		if not normalized:
			raise ValueError(f"station-id 非法: {args.station_id}")
		station_filter = {normalized}
	temperature_idx = TEMPERATURE_FIELD_INDEX[args.temperature_field]

	monthly_records: list[dict] = []
	month_to_values: Dict[int, list[float]] = defaultdict(list)

	files = list(find_tem_files(args.data_dir))
	if not files:
		raise FileNotFoundError(
			f"在目录 {args.data_dir} 下未找到匹配文件: SURF_CLI_CHN_MUL_DAY-TEM-12001-YYYYMM.TXT"
		)

	total_files = len(files)
	start_time = time.time()

	for index, (year, month, path) in enumerate(files, start=1):
		print_progress(index, total_files, path, start_time)
		station_sum_and_count = process_one_file(path, temperature_idx, station_filter)

		station_means = []
		for station_id, (temp_sum, valid_days) in station_sum_and_count.items():
			if valid_days <= 0:
				continue
			station_means.append(temp_sum / valid_days)

		station_count = len(station_means)
		if station_count == 0:
			region_avg = None
		else:
			region_avg = sum(station_means) / station_count
			month_to_values[month].append(region_avg)

		monthly_records.append(
			{
				"year": year,
				"month": month,
				"yyyymm": f"{year:04d}{month:02d}",
				"station_count": station_count,
				"region_avg_temperature_c": "" if region_avg is None else round(region_avg, 3),
				"source_file": path.name,
			}
		)

	print()

	climatology_records: list[dict] = []
	for month in range(1, 13):
		vals = month_to_values.get(month, [])
		if vals:
			climatology_avg = sum(vals) / len(vals)
			climatology_records.append(
				{
					"month": month,
					"year_count": len(vals),
					"climatology_avg_temperature_c": round(climatology_avg, 3),
				}
			)
		else:
			climatology_records.append(
				{
					"month": month,
					"year_count": 0,
					"climatology_avg_temperature_c": "",
				}
			)

	write_monthly_csv(args.output_monthly, monthly_records)
	write_climatology_csv(args.output_climatology, climatology_records)

	print(f"完成。共处理文件: {len(files)}")
	if args.station_id is not None:
		print(f"目标台站: {next(iter(station_filter))}")
	print(f"逐月结果: {args.output_monthly}")
	print(f"多年各月平均结果: {args.output_climatology}")


if __name__ == "__main__":
	main()
