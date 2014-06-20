function get_config_file ()
{
	config_file="$HOME/.netqualrc"
	if [ -n "$NQ_CONFIG_DIR" ]; then
		config_file="$NQ_CONFIG_DIR/.netqualrc"
	fi

	echo $config_file
	return 0
}

function load_config_file()
{
	config_file=$(get_config_file)
	if ! source "$config_file"; then
		echo "failed to load config file" >/dev/error
		return 1
	fi

	return 0
}

function have_interface ()
{
	ifname=$1
	if ! ip addr show dev "$ifname" >/dev/null 2>&1; then
		return 1
	fi
	return 0
}

function get_interface ()
{
	load_config_file

	iftype=$1

	if have_interface "$iftype"; then
		echo "$iftype"
		return 0
	fi

	varname="INTERFACE_$iftype"
	name_from_conf=${!varname}

	if [ -n "$name_from_conf" ]; then
		if have_interface "$name_from_conf"; then
			echo "$name_from_conf"
			return 0
		else
			return 1
		fi
	fi
}
