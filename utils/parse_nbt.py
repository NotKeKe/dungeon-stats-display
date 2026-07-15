import base64
import gzip
import io
from nbt import nbt
import json

def _nbt_to_dict(nbt_obj):
    """
    遞迴將 NBT 物件轉換為 Python 原生 dict/list
    """
    # 如果是 Compound 型態（類似 dict）
    if isinstance(nbt_obj, nbt.TAG_Compound):
        return {key: _nbt_to_dict(value) for key, value in nbt_obj.iteritems()}
    
    # 如果是 List 型態（類似 list）
    elif isinstance(nbt_obj, nbt.TAG_List):
        return [_nbt_to_dict(item) for item in nbt_obj]
    
    # 如果是 Byte Array 或 Int Array，轉為普通的 Python list
    elif isinstance(nbt_obj, (nbt.TAG_Byte_Array, nbt.TAG_Int_Array)):
        return list(nbt_obj.value)
    
    # 基本型態（String, Int, Float, Long 等），直接取其 value
    else:
        return nbt_obj.value

def decode_nbt_base64(base64_str) -> list[dict]:
    """將 nbt base64 解碼成 python dict

    Args:
        base64_str (_type_): _description_

    Returns:
        list[dict]: _description_
    """    
    # 1. Base64 解碼
    compressed_data = base64.b64decode(base64_str)
    
    # 3. 使用 NBT 函式庫解析二進位資料
    nbt_file = nbt.NBTFile(fileobj=io.BytesIO(compressed_data))
    
    # 4. 將 NBT 物件轉換為 Python 原生 dict
    parsed_data = _nbt_to_dict(nbt_file)

    return parsed_data['i']