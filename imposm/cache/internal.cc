#include <Python.h>
#include <string>
#include "structmember.h"
#include "internal.pb.h"


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

      imposm::cache::internal::DeltaCoords *protobuf;
  } DeltaCoords;

  static void
  DeltaCoords_dealloc(DeltaCoords* self)
  {
      self->ob_type->tp_free((PyObject*)self);

      delete self->protobuf;
  }

  static PyObject *
  DeltaCoords_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
  {
      DeltaCoords *self;

      self = (DeltaCoords *)type->tp_alloc(type, 0);

      self->protobuf = new imposm::cache::internal::DeltaCoords();

      return (PyObject *)self;
  }

  static PyObject *
  DeltaCoords_SerializeToString(DeltaCoords* self)
  {
      std::string result;
      self->protobuf->SerializeToString(&result);
      return PyString_FromStringAndSize(result.data(), result.length());
  }


  static PyObject *
  DeltaCoords_ParseFromString(DeltaCoords* self, PyObject *value)
  {
      std::string serialized(PyString_AsString(value), PyString_Size(value));
      self->protobuf->ParseFromString(serialized);
      Py_RETURN_NONE;
  }


  
    

    static PyObject *
    DeltaCoords_getids(DeltaCoords *self, void *closure)
    {
        
          int len = self->protobuf->ids_size();
          PyObject *tuple = PyTuple_New(len);
          for (int i = 0; i < len; ++i) {
            PyObject *value =
                fastpb_convert18(
                    self->protobuf->ids(i));
            PyTuple_SetItem(tuple, i, value);
          }
          return tuple;

        
    }

    static int
    DeltaCoords_setids(DeltaCoords *self, PyObject *input, void *closure)
    {
      if (input == NULL || input == Py_None) {
        self->protobuf->clear_ids();
        return 0;
      }

      
        if (PyString_Check(input)) {
          PyErr_SetString(PyExc_TypeError, "The ids attribute value must be a sequence");
          return -1;
        }
        PyObject *sequence = PySequence_Fast(input, "The ids attribute value must be a sequence");
        self->protobuf->clear_ids();
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
                          "The ids attribute value must be an integer");
          return -1;
        }

      

      
          
            self->protobuf->add_ids(protoValue);
          
        }

        Py_XDECREF(sequence);
      

      return 0;
    }
  
    

    static PyObject *
    DeltaCoords_getlats(DeltaCoords *self, void *closure)
    {
        
          int len = self->protobuf->lats_size();
          PyObject *tuple = PyTuple_New(len);
          for (int i = 0; i < len; ++i) {
            PyObject *value =
                fastpb_convert18(
                    self->protobuf->lats(i));
            PyTuple_SetItem(tuple, i, value);
          }
          return tuple;

        
    }

    static int
    DeltaCoords_setlats(DeltaCoords *self, PyObject *input, void *closure)
    {
      if (input == NULL || input == Py_None) {
        self->protobuf->clear_lats();
        return 0;
      }

      
        if (PyString_Check(input)) {
          PyErr_SetString(PyExc_TypeError, "The lats attribute value must be a sequence");
          return -1;
        }
        PyObject *sequence = PySequence_Fast(input, "The lats attribute value must be a sequence");
        self->protobuf->clear_lats();
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
                          "The lats attribute value must be an integer");
          return -1;
        }

      

      
          
            self->protobuf->add_lats(protoValue);
          
        }

        Py_XDECREF(sequence);
      

      return 0;
    }
  
    

    static PyObject *
    DeltaCoords_getlons(DeltaCoords *self, void *closure)
    {
        
          int len = self->protobuf->lons_size();
          PyObject *tuple = PyTuple_New(len);
          for (int i = 0; i < len; ++i) {
            PyObject *value =
                fastpb_convert18(
                    self->protobuf->lons(i));
            PyTuple_SetItem(tuple, i, value);
          }
          return tuple;

        
    }

    static int
    DeltaCoords_setlons(DeltaCoords *self, PyObject *input, void *closure)
    {
      if (input == NULL || input == Py_None) {
        self->protobuf->clear_lons();
        return 0;
      }

      
        if (PyString_Check(input)) {
          PyErr_SetString(PyExc_TypeError, "The lons attribute value must be a sequence");
          return -1;
        }
        PyObject *sequence = PySequence_Fast(input, "The lons attribute value must be a sequence");
        self->protobuf->clear_lons();
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
                          "The lons attribute value must be an integer");
          return -1;
        }

      

      
          
            self->protobuf->add_lons(protoValue);
          
        }

        Py_XDECREF(sequence);
      

      return 0;
    }
  

  static int
  DeltaCoords_init(DeltaCoords *self, PyObject *args, PyObject *kwds)
  {
      
        
          PyObject *ids = NULL;
        
          PyObject *lats = NULL;
        
          PyObject *lons = NULL;
        

        static char *kwlist[] = {
          
            (char *) "ids",
          
            (char *) "lats",
          
            (char *) "lons",
          
          NULL
        };

        if (! PyArg_ParseTupleAndKeywords(
            args, kwds, "|OOO", kwlist,
            &ids,&lats,&lons))
          return -1;

        
          if (ids) {
            if (DeltaCoords_setids(self, ids, NULL) < 0) {
              return -1;
            }
          }
        
          if (lats) {
            if (DeltaCoords_setlats(self, lats, NULL) < 0) {
              return -1;
            }
          }
        
          if (lons) {
            if (DeltaCoords_setlons(self, lons, NULL) < 0) {
              return -1;
            }
          }
        
      

      return 0;
  }

  static PyMemberDef DeltaCoords_members[] = {
      {NULL}  // Sentinel
  };


  static PyGetSetDef DeltaCoords_getsetters[] = {
    
      {(char *)"ids",
       (getter)DeltaCoords_getids, (setter)DeltaCoords_setids,
       (char *)"",
       NULL},
    
      {(char *)"lats",
       (getter)DeltaCoords_getlats, (setter)DeltaCoords_setlats,
       (char *)"",
       NULL},
    
      {(char *)"lons",
       (getter)DeltaCoords_getlons, (setter)DeltaCoords_setlons,
       (char *)"",
       NULL},
    
      {NULL}  // Sentinel
  };


  static PyMethodDef DeltaCoords_methods[] = {
      {"SerializeToString", (PyCFunction)DeltaCoords_SerializeToString, METH_NOARGS,
       "Serializes the protocol buffer to a string."
      },
      {"ParseFromString", (PyCFunction)DeltaCoords_ParseFromString, METH_O,
       "Parses the protocol buffer from a string."
      },
      {NULL}  // Sentinel
  };


  static PyTypeObject DeltaCoordsType = {
      PyObject_HEAD_INIT(NULL)
      0,                                      /*ob_size*/
      "imposm.cache.internal.DeltaCoords",  /*tp_name*/
      sizeof(DeltaCoords),             /*tp_basicsize*/
      0,                                      /*tp_itemsize*/
      (destructor)DeltaCoords_dealloc, /*tp_dealloc*/
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
      "DeltaCoords objects",           /* tp_doc */
      0,                                      /* tp_traverse */
      0,                                      /* tp_clear */
      0,                   	 	                /* tp_richcompare */
      0,	   	                                /* tp_weaklistoffset */
      0,                   		                /* tp_iter */
      0,		                                  /* tp_iternext */
      DeltaCoords_methods,             /* tp_methods */
      DeltaCoords_members,             /* tp_members */
      DeltaCoords_getsetters,          /* tp_getset */
      0,                                      /* tp_base */
      0,                                      /* tp_dict */
      0,                                      /* tp_descr_get */
      0,                                      /* tp_descr_set */
      0,                                      /* tp_dictoffset */
      (initproc)DeltaCoords_init,      /* tp_init */
      0,                                      /* tp_alloc */
      DeltaCoords_new,                 /* tp_new */
  };


  typedef struct {
      PyObject_HEAD

      imposm::cache::internal::DeltaList *protobuf;
  } DeltaList;

  static void
  DeltaList_dealloc(DeltaList* self)
  {
      self->ob_type->tp_free((PyObject*)self);

      delete self->protobuf;
  }

  static PyObject *
  DeltaList_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
  {
      DeltaList *self;

      self = (DeltaList *)type->tp_alloc(type, 0);

      self->protobuf = new imposm::cache::internal::DeltaList();

      return (PyObject *)self;
  }

  static PyObject *
  DeltaList_SerializeToString(DeltaList* self)
  {
      std::string result;
      self->protobuf->SerializeToString(&result);
      return PyString_FromStringAndSize(result.data(), result.length());
  }


  static PyObject *
  DeltaList_ParseFromString(DeltaList* self, PyObject *value)
  {
      std::string serialized(PyString_AsString(value), PyString_Size(value));
      self->protobuf->ParseFromString(serialized);
      Py_RETURN_NONE;
  }


  
    

    static PyObject *
    DeltaList_getids(DeltaList *self, void *closure)
    {
        
          int len = self->protobuf->ids_size();
          PyObject *tuple = PyTuple_New(len);
          for (int i = 0; i < len; ++i) {
            PyObject *value =
                fastpb_convert18(
                    self->protobuf->ids(i));
            PyTuple_SetItem(tuple, i, value);
          }
          return tuple;

        
    }

    static int
    DeltaList_setids(DeltaList *self, PyObject *input, void *closure)
    {
      if (input == NULL || input == Py_None) {
        self->protobuf->clear_ids();
        return 0;
      }

      
        if (PyString_Check(input)) {
          PyErr_SetString(PyExc_TypeError, "The ids attribute value must be a sequence");
          return -1;
        }
        PyObject *sequence = PySequence_Fast(input, "The ids attribute value must be a sequence");
        self->protobuf->clear_ids();
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
                          "The ids attribute value must be an integer");
          return -1;
        }

      

      
          
            self->protobuf->add_ids(protoValue);
          
        }

        Py_XDECREF(sequence);
      

      return 0;
    }
  

  static int
  DeltaList_init(DeltaList *self, PyObject *args, PyObject *kwds)
  {
      
        
          PyObject *ids = NULL;
        

        static char *kwlist[] = {
          
            (char *) "ids",
          
          NULL
        };

        if (! PyArg_ParseTupleAndKeywords(
            args, kwds, "|O", kwlist,
            &ids))
          return -1;

        
          if (ids) {
            if (DeltaList_setids(self, ids, NULL) < 0) {
              return -1;
            }
          }
        
      

      return 0;
  }

  static PyMemberDef DeltaList_members[] = {
      {NULL}  // Sentinel
  };


  static PyGetSetDef DeltaList_getsetters[] = {
    
      {(char *)"ids",
       (getter)DeltaList_getids, (setter)DeltaList_setids,
       (char *)"",
       NULL},
    
      {NULL}  // Sentinel
  };


  static PyMethodDef DeltaList_methods[] = {
      {"SerializeToString", (PyCFunction)DeltaList_SerializeToString, METH_NOARGS,
       "Serializes the protocol buffer to a string."
      },
      {"ParseFromString", (PyCFunction)DeltaList_ParseFromString, METH_O,
       "Parses the protocol buffer from a string."
      },
      {NULL}  // Sentinel
  };


  static PyTypeObject DeltaListType = {
      PyObject_HEAD_INIT(NULL)
      0,                                      /*ob_size*/
      "imposm.cache.internal.DeltaList",  /*tp_name*/
      sizeof(DeltaList),             /*tp_basicsize*/
      0,                                      /*tp_itemsize*/
      (destructor)DeltaList_dealloc, /*tp_dealloc*/
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
      "DeltaList objects",           /* tp_doc */
      0,                                      /* tp_traverse */
      0,                                      /* tp_clear */
      0,                   	 	                /* tp_richcompare */
      0,	   	                                /* tp_weaklistoffset */
      0,                   		                /* tp_iter */
      0,		                                  /* tp_iternext */
      DeltaList_methods,             /* tp_methods */
      DeltaList_members,             /* tp_members */
      DeltaList_getsetters,          /* tp_getset */
      0,                                      /* tp_base */
      0,                                      /* tp_dict */
      0,                                      /* tp_descr_get */
      0,                                      /* tp_descr_set */
      0,                                      /* tp_dictoffset */
      (initproc)DeltaList_init,      /* tp_init */
      0,                                      /* tp_alloc */
      DeltaList_new,                 /* tp_new */
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

    

    
      if (PyType_Ready(&DeltaCoordsType) < 0)
          return;
    
      if (PyType_Ready(&DeltaListType) < 0)
          return;
    

    m = Py_InitModule3("internal", module_methods,
                       "");

    if (m == NULL)
      return;

    

    
      Py_INCREF(&DeltaCoordsType);
      PyModule_AddObject(m, "DeltaCoords", (PyObject *)&DeltaCoordsType);
    
      Py_INCREF(&DeltaListType);
      PyModule_AddObject(m, "DeltaList", (PyObject *)&DeltaListType);
    
}