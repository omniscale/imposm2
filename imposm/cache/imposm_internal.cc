#include <Python.h>
#include <string>
#include "structmember.h"
#include "imposm_internal.pb.h"


static PyObject *
fastpb_convert5(::google::protobuf::int32 value)
{
    return PyLong_FromLong(value);
}

static PyObject *
fastpb_convert3(::google::protobuf::int64 value)
{
    return PyLong_FromLongLong(value);
}

static PyObject *
fastpb_convert18(::google::protobuf::int64 value)
{
    return PyLong_FromLongLong(value);
}

static PyObject *
fastpb_convert17(::google::protobuf::int32 value)
{
    return PyLong_FromLong(value);
}

static PyObject *
fastpb_convert13(::google::protobuf::uint32 value)
{
    return PyLong_FromUnsignedLong(value);
}

static PyObject *
fastpb_convert4(::google::protobuf::uint64 value)
{
    return PyLong_FromUnsignedLong(value);
}

static PyObject *
fastpb_convert1(double value)
{
    return PyFloat_FromDouble(value);
}

static PyObject *
fastpb_convert2(float value)
{
   return PyFloat_FromDouble(value);
}

static PyObject *
fastpb_convert9(const ::std::string &value)
{
    return PyUnicode_Decode(value.data(), value.length(), "utf-8", NULL);
}

static PyObject *
fastpb_convert12(const ::std::string &value)
{
    return PyString_FromStringAndSize(value.data(), value.length());
}

static PyObject *
fastpb_convert8(bool value)
{
    return PyBool_FromLong(value ? 1 : 0);
}

static PyObject *
fastpb_convert14(int value)
{
    // TODO(robbyw): Check EnumName_IsValid(value)
    return PyLong_FromLong(value);
}




  typedef struct {
      PyObject_HEAD

      imposm::cache::internal::DeltaNodes *protobuf;
  } DeltaNodes;

  static void
  DeltaNodes_dealloc(DeltaNodes* self)
  {
      self->ob_type->tp_free((PyObject*)self);

      delete self->protobuf;
  }

  static PyObject *
  DeltaNodes_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
  {
      DeltaNodes *self;

      self = (DeltaNodes *)type->tp_alloc(type, 0);

      self->protobuf = new imposm::cache::internal::DeltaNodes();

      return (PyObject *)self;
  }

  static PyObject *
  DeltaNodes_SerializeToString(DeltaNodes* self)
  {
      std::string result;
      self->protobuf->SerializeToString(&result);
      return PyString_FromStringAndSize(result.data(), result.length());
  }


  static PyObject *
  DeltaNodes_ParseFromString(DeltaNodes* self, PyObject *value)
  {
      std::string serialized(PyString_AsString(value), PyString_Size(value));
      self->protobuf->ParseFromString(serialized);
      Py_RETURN_NONE;
  }


  
    

    static PyObject *
    DeltaNodes_getid(DeltaNodes *self, void *closure)
    {
        
          int len = self->protobuf->id_size();
          PyObject *tuple = PyTuple_New(len);
          for (int i = 0; i < len; ++i) {
            PyObject *value =
                fastpb_convert18(
                    self->protobuf->id(i));
            PyTuple_SetItem(tuple, i, value);
          }
          return tuple;

        
    }

    static int
    DeltaNodes_setid(DeltaNodes *self, PyObject *input, void *closure)
    {
      if (input == NULL || input == Py_None) {
        self->protobuf->clear_id();
        return 0;
      }

      
        if (PyString_Check(input)) {
          PyErr_SetString(PyExc_TypeError, "The id attribute value must be a sequence");
          return -1;
        }
        PyObject *sequence = PySequence_Fast(input, "The id attribute value must be a sequence");
        self->protobuf->clear_id();
        for (Py_ssize_t i = 0, len = PySequence_Length(sequence); i < len; ++i) {
          PyObject *value = PySequence_Fast_GET_ITEM(sequence, i);

      

      
        ::google::protobuf::int64 protoValue;

        // int64
        if (PyInt_Check(value)) {
          protoValue = PyInt_AsLong(value);
        } else if (PyLong_Check(value)) {
          protoValue = PyLong_AsLongLong(value);
        } else {
          PyErr_SetString(PyExc_TypeError,
                          "The id attribute value must be an integer");
          return -1;
        }

      

      
          
            self->protobuf->add_id(protoValue);
          
        }

        Py_XDECREF(sequence);
      

      return 0;
    }
  
    

    static PyObject *
    DeltaNodes_getlat(DeltaNodes *self, void *closure)
    {
        
          int len = self->protobuf->lat_size();
          PyObject *tuple = PyTuple_New(len);
          for (int i = 0; i < len; ++i) {
            PyObject *value =
                fastpb_convert17(
                    self->protobuf->lat(i));
            PyTuple_SetItem(tuple, i, value);
          }
          return tuple;

        
    }

    static int
    DeltaNodes_setlat(DeltaNodes *self, PyObject *input, void *closure)
    {
      if (input == NULL || input == Py_None) {
        self->protobuf->clear_lat();
        return 0;
      }

      
        if (PyString_Check(input)) {
          PyErr_SetString(PyExc_TypeError, "The lat attribute value must be a sequence");
          return -1;
        }
        PyObject *sequence = PySequence_Fast(input, "The lat attribute value must be a sequence");
        self->protobuf->clear_lat();
        for (Py_ssize_t i = 0, len = PySequence_Length(sequence); i < len; ++i) {
          PyObject *value = PySequence_Fast_GET_ITEM(sequence, i);

      

      
        ::google::protobuf::int32 protoValue;

        // int32
        if (PyInt_Check(value)) {
          protoValue = PyInt_AsLong(value);
        } else {
          PyErr_SetString(PyExc_TypeError,
                          "The lat attribute value must be an integer");
          return -1;
        }
        
      

      
          
            self->protobuf->add_lat(protoValue);
          
        }

        Py_XDECREF(sequence);
      

      return 0;
    }
  
    

    static PyObject *
    DeltaNodes_getlon(DeltaNodes *self, void *closure)
    {
        
          int len = self->protobuf->lon_size();
          PyObject *tuple = PyTuple_New(len);
          for (int i = 0; i < len; ++i) {
            PyObject *value =
                fastpb_convert17(
                    self->protobuf->lon(i));
            PyTuple_SetItem(tuple, i, value);
          }
          return tuple;

        
    }

    static int
    DeltaNodes_setlon(DeltaNodes *self, PyObject *input, void *closure)
    {
      if (input == NULL || input == Py_None) {
        self->protobuf->clear_lon();
        return 0;
      }

      
        if (PyString_Check(input)) {
          PyErr_SetString(PyExc_TypeError, "The lon attribute value must be a sequence");
          return -1;
        }
        PyObject *sequence = PySequence_Fast(input, "The lon attribute value must be a sequence");
        self->protobuf->clear_lon();
        for (Py_ssize_t i = 0, len = PySequence_Length(sequence); i < len; ++i) {
          PyObject *value = PySequence_Fast_GET_ITEM(sequence, i);

      

      
        ::google::protobuf::int32 protoValue;

        // int32
        if (PyInt_Check(value)) {
          protoValue = PyInt_AsLong(value);
        } else {
          PyErr_SetString(PyExc_TypeError,
                          "The lon attribute value must be an integer");
          return -1;
        }
        
      

      
          
            self->protobuf->add_lon(protoValue);
          
        }

        Py_XDECREF(sequence);
      

      return 0;
    }
  

  static int
  DeltaNodes_init(DeltaNodes *self, PyObject *args, PyObject *kwds)
  {
      
        
          PyObject *id = NULL;
        
          PyObject *lat = NULL;
        
          PyObject *lon = NULL;
        

        static char *kwlist[] = {
          
            (char *) "id",
          
            (char *) "lat",
          
            (char *) "lon",
          
          NULL
        };

        if (! PyArg_ParseTupleAndKeywords(
            args, kwds, "|OOO", kwlist,
            &id,&lat,&lon))
          return -1;

        
          if (id) {
            if (DeltaNodes_setid(self, id, NULL) < 0) {
              return -1;
            }
          }
        
          if (lat) {
            if (DeltaNodes_setlat(self, lat, NULL) < 0) {
              return -1;
            }
          }
        
          if (lon) {
            if (DeltaNodes_setlon(self, lon, NULL) < 0) {
              return -1;
            }
          }
        
      

      return 0;
  }

  static PyMemberDef DeltaNodes_members[] = {
      {NULL}  // Sentinel
  };


  static PyGetSetDef DeltaNodes_getsetters[] = {
    
      {(char *)"id",
       (getter)DeltaNodes_getid, (setter)DeltaNodes_setid,
       (char *)"",
       NULL},
    
      {(char *)"lat",
       (getter)DeltaNodes_getlat, (setter)DeltaNodes_setlat,
       (char *)"",
       NULL},
    
      {(char *)"lon",
       (getter)DeltaNodes_getlon, (setter)DeltaNodes_setlon,
       (char *)"",
       NULL},
    
      {NULL}  // Sentinel
  };


  static PyMethodDef DeltaNodes_methods[] = {
      {"SerializeToString", (PyCFunction)DeltaNodes_SerializeToString, METH_NOARGS,
       "Serializes the protocol buffer to a string."
      },
      {"ParseFromString", (PyCFunction)DeltaNodes_ParseFromString, METH_O,
       "Parses the protocol buffer from a string."
      },
      {NULL}  // Sentinel
  };


  static PyTypeObject DeltaNodesType = {
      PyObject_HEAD_INIT(NULL)
      0,                                      /*ob_size*/
      "imposm.cache.internal.DeltaNodes",  /*tp_name*/
      sizeof(DeltaNodes),             /*tp_basicsize*/
      0,                                      /*tp_itemsize*/
      (destructor)DeltaNodes_dealloc, /*tp_dealloc*/
      0,                                      /*tp_print*/
      0,                                      /*tp_getattr*/
      0,                                      /*tp_setattr*/
      0,                                      /*tp_compare*/
      0,                                      /*tp_repr*/
      0,                                      /*tp_as_number*/
      0,                                      /*tp_as_sequence*/
      0,                                      /*tp_as_mapping*/
      0,                                      /*tp_hash */
      0,                                      /*tp_call*/
      0,                                      /*tp_str*/
      0,                                      /*tp_getattro*/
      0,                                      /*tp_setattro*/
      0,                                      /*tp_as_buffer*/
      Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE, /*tp_flags*/
      "DeltaNodes objects",           /* tp_doc */
      0,                                      /* tp_traverse */
      0,                                      /* tp_clear */
      0,                   	 	                /* tp_richcompare */
      0,	   	                                /* tp_weaklistoffset */
      0,                   		                /* tp_iter */
      0,		                                  /* tp_iternext */
      DeltaNodes_methods,             /* tp_methods */
      DeltaNodes_members,             /* tp_members */
      DeltaNodes_getsetters,          /* tp_getset */
      0,                                      /* tp_base */
      0,                                      /* tp_dict */
      0,                                      /* tp_descr_get */
      0,                                      /* tp_descr_set */
      0,                                      /* tp_dictoffset */
      (initproc)DeltaNodes_init,      /* tp_init */
      0,                                      /* tp_alloc */
      DeltaNodes_new,                 /* tp_new */
  };



static PyMethodDef module_methods[] = {
    {NULL}  // Sentinel
};

#ifndef PyMODINIT_FUNC	// Declarations for DLL import/export.
#define PyMODINIT_FUNC void
#endif
PyMODINIT_FUNC
initinternal(void)
{
    GOOGLE_PROTOBUF_VERIFY_VERSION;

    PyObject* m;

    

    
      if (PyType_Ready(&DeltaNodesType) < 0)
          return;
    

    m = Py_InitModule3("internal", module_methods,
                       "");

    if (m == NULL)
      return;

    

    
      Py_INCREF(&DeltaNodesType);
      PyModule_AddObject(m, "DeltaNodes", (PyObject *)&DeltaNodesType);
    
}