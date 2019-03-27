create or replace function fnc_table_to_mysql  
( i_owner                       in string,  
  i_table_name                  in string,  
  i_number_default_type         in string := 'decimal',  
  i_auto_incretment_column_name in string := '%ID'  
)  
/*  
  功能：ORACLE表生成MYSQL建表DDL  
  作者：叶正盛 2013-07-27  
  新浪微博:@yzsind-叶正盛  
  参数说明：  
  i_owner:schema名  
  i_table_name:表名  
  i_number_default_type:NUMBER默认转换的类型，缺省是decimal  
  i_auto_incretment_column_name:自增属性字段名称规则，默认是%ID  

  已知问题：  
  1.不支持分区  
  2.不支持函数索引，位图索引等特殊索引定义  
  3.不支持自定义数据类型，不支持ROWID,RAW等特殊数据类型  
  4.不支持外键  
  5.不支持自定义约束  
  6.不支持与空间、事务相关属性  
  7.DATE与TIMESTAMP转换成datetime，需注意精度  
  8.超大NUMBER直接转换为bigint，需注意精度  
  9.auto incretment 是根据字段名规则加一些判断，设置不一定准确，需检查  
  */  
 return clob is  
  Result         clob;  
  cnt            number;  
  data_type      varchar2(128);  
  column_str     varchar2(4000);  
  pk_str         varchar2(4000);  
  table_comments varchar2(4000);  
  is_pk_column   number := 0;  
begin  
  select count(*)  
    into cnt  
    from all_tables  
   where owner = i_owner  
     and table_name = i_table_name;  
  if (cnt = 0) then  
    RAISE_APPLICATION_ERROR(-20000,'can''t found table,please check input!');  
  else  
    Result := 'CREATE TABLE `' || lower(i_table_name) || '`(';  
    --column  
    for c in (select a.column_name,  
                     a.data_type,  
                     a.data_length,  
                     a.data_precision,  
                     a.data_scale,  
                     a.nullable,  
                     a.data_default,  
                     b.COMMENTS  
                from all_tab_cols a, all_col_comments b  
               where a.owner = i_owner  
                 and a.table_name = i_table_name  
                 and a.HIDDEN_COLUMN = 'NO'  
                 and a.owner = b.OWNER  
                 and a.TABLE_NAME = b.TABLE_NAME  
                 and a.COLUMN_NAME = b.COLUMN_NAME  
               order by a.column_id) loop  
      if ((c.data_type = 'VARCHAR2' or c.data_type = 'NVARCHAR2') and c.data_length < 1000) then  
        data_type := 'varchar(' || c.data_length || ')';  
	  elsif ((c.data_type = 'VARCHAR2' or c.data_type = 'NVARCHAR2') and c.data_length >= 1000) then
		data_type := 'text';
      elsif (c.data_type = 'CHAR' or c.data_type = 'NCHAR') then  
        data_type := 'char(' || c.data_length || ')';  
      elsif (c.data_type = 'NUMBER') then  
        if (c.column_name like '%ID' and c.data_scale is null) then  
          data_type := 'bigint';  
        elsif (c.data_precision<3 and c.data_scale = 0) then  
          data_type := 'tinyint';  
        elsif (c.data_precision<5 and c.data_scale = 0) then  
          data_type := 'smallint';  
        elsif (c.data_precision<10 and c.data_scale = 0) then  
          data_type := 'int';  
        elsif (c.data_precision is not null and c.data_scale = 0) then  
          data_type := 'bigint';  
        elsif (c.data_precision is not null and c.data_scale is not null) then  
          data_type := 'decimal(' || c.data_precision || ',' ||  
                       c.data_scale || ')';  
        else  
          data_type := i_number_default_type;  
        end if;  
      elsif (c.data_type = 'DATE' or c.data_type like 'TIMESTAMP%') then  
        data_type := 'datetime';  
      elsif (c.data_type = 'CLOB' or c.data_type = 'NCLOB' or  
            c.data_type = 'LONG') then  
        data_type := 'text';  
      elsif (c.data_type = 'BLOB' or c.data_type = 'LONG RAW') then  
        data_type := 'blob';  
      elsif (c.data_type = 'BINARY_FLOAT') then  
        data_type := 'float';  
      elsif (c.data_type = 'BINARY_DOUBLE') then  
        data_type := 'double';  
      else  
        data_type := c.data_type;  
      end if;  
      column_str := '  `' || lower(c.column_name) || '` ' || data_type;  
      if (c.column_name like i_auto_incretment_column_name and  
         (c.data_scale is null or c.data_scale = 0)) then  
        select count(*)  
          into is_pk_column  
          from all_constraints a, all_cons_columns b  
         where a.owner = i_owner  
           and a.table_name = i_table_name  
           and a.constraint_type = 'P'  
           and a.OWNER = b.OWNER  
           and a.TABLE_NAME = b.TABLE_NAME  
           and a.CONSTRAINT_NAME = b.CONSTRAINT_NAME  
           and b.COLUMN_NAME = c.column_name;  
        if is_pk_column > 0 then  
          column_str := column_str || ' AUTO_INCREMENT';  
        end if;  
      end if;  
      if c.nullable = 'NO' then  
        column_str := column_str || ' NOT NULL';  
      end if;  
      if (trim(c.data_default) is not null) then  
        column_str := column_str || ' DEFAULT ' ||  
                      trim(replace(replace(c.data_default, chr(13), ''),  
                                   chr(10),  
                                   ''));  
      end if;  
      if c.comments is not null then  
        column_str := column_str || ' COMMENT ''' || c.comments || '''';  
      end if;  
      Result := Result || chr(10) || column_str || ',';  
    end loop;  
    --pk  
    for c in (select a.constraint_name, wm_concat(a.column_name) pk_columns  
                from (select a.CONSTRAINT_NAME,  
                             '`' || b.COLUMN_NAME || '`' column_name  
                        from all_constraints a, all_cons_columns b  
                       where a.owner = i_owner  
                         and a.table_name = i_table_name  
                         and a.constraint_type = 'P'  
                         and a.OWNER = b.OWNER  
                         and a.TABLE_NAME = b.TABLE_NAME  
                         and a.CONSTRAINT_NAME = b.CONSTRAINT_NAME  
                       order by b.POSITION) a  
               group by a.constraint_name) loop  
      Result := Result || chr(10) || '  PRIMARY KEY (' ||  
                lower(c.pk_columns) || '),';  
    end loop;  
    --unique  
    for c in (select a.constraint_name, wm_concat(a.column_name) uk_columns  
                from (select a.CONSTRAINT_NAME,  
                             '`' || b.COLUMN_NAME || '`' column_name  
                        from all_constraints a, all_cons_columns b  
                       where a.owner = i_owner  
                         and a.table_name = i_table_name  
                         and a.constraint_type = 'U'  
                         and a.OWNER = b.OWNER  
                         and a.TABLE_NAME = b.TABLE_NAME  
                         and a.CONSTRAINT_NAME = b.CONSTRAINT_NAME  
                       order by b.POSITION) a  
               group by a.constraint_name) loop  
      Result := Result || chr(10) || '  UNIQUE KEY `' ||  
                lower(c.constraint_name) || '`(' || lower(c.uk_columns) || '),';  
    end loop;  
    -- index  
    for c in (select a.index_name, wm_concat(a.column_name) ind_columns  
                from (select a.index_name,  
                             '`' || a.COLUMN_NAME || '`' column_name  
                        from all_ind_columns a  
                       where a.table_owner = i_owner  
                         and a.TABLE_NAME = i_table_name  
                         and not exists  
                       (select index_name  
                                from all_constraints b  
                               where a.TABLE_OWNER = b.owner  
                                 and a.TABLE_NAME = b.TABLE_NAME  
                                 and a.INDEX_NAME = b.INDEX_NAME)  
                       order by a.COLUMN_POSITION) a  
               group by a.index_name) loop  
      Result := Result || chr(10) || '  KEY `' || lower(c.index_name) || '`(' ||  
                lower(c.ind_columns) || '),';  
    end loop;  
    Result := substr(Result, 1, length(result) - 1) || chr(10) || ')';  
    --table comments  
    select max(a.COMMENTS)  
      into table_comments  
      from all_tab_comments a  
     where owner = i_owner  
       and table_name = i_table_name;  
    if (table_comments is not null) then  
      Result := Result || 'COMMENT=''' || table_comments || '''';  
    end if;  
    Result := Result || ';';  
  end if;  
  return(Result);  
end fnc_table_to_mysql;  
/