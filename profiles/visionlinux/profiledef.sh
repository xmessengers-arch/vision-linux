# Vision Linux archiso profile

iso_name="visionlinux"
iso_publisher="Vision Linux <team@visionlinux.dev>"
iso_application="Vision Linux"
iso_version="2026.09.06"
iso_label="VISIONLINUX"
iso_directory="visionlinux"
install_dir="visionlinux"
buildmodes=('iso')
bootmodes=('bios.syslinux'
           'uefi.systemd-boot')
pacman_conf="pacman.conf"
airootfs_image_type="squashfs"
airootfs_image_tool_options=('-comp' 'xz' '-b' '1M' '-Xdict-size' '1M')
file_permissions=(
  ["/etc/shadow"]="0:0:400"
  ["/root"]="0:0:750"
)
