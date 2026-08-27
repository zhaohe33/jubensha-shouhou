# 背景图目录

网站上传背景图时，会自动把图片提交到这个目录。

## 自动上传流程

1. 打开网站：https://zhaohe33.github.io/jubensha-aftersale/
2. 在「GitHub 自动上传」里填写你的 **GitHub Token**（只保存在本机浏览器）
3. 上传背景图
4. 图片会自动推到本仓库 `images/` 目录，并填入 jsDelivr 链接

## 创建 Token

1. 打开：https://github.com/settings/tokens/new?scopes=repo&description=jubensha-bg-upload
2. 勾选 `repo` 权限（或 Fine-grained Token 对该仓库的 Contents 读写）
3. 生成后复制 Token，粘贴到网站里

## 链接格式

上传成功后会自动使用：

`https://cdn.jsdelivr.net/gh/zhaohe33/jubensha-aftersale@master/images/文件名.jpg`

也可手动使用 Raw 链接：

`https://raw.githubusercontent.com/zhaohe33/jubensha-aftersale/master/images/文件名.jpg`
